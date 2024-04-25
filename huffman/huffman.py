"""
Functions dealing with GBAFE Huffman encoding/decoding and friends.
"""

import bisect
from collections.abc import Iterator, Iterable

from rom import Rom

def node_next_idx(node : int, which_bit : int) -> int:
    return (node >> (16 * which_bit)) & 0xFFFF

def decode_tree(rom : Rom, tree_offset : int, root_offset : int) -> list[int]:
    """
    Decodes the existing Huffman tree from the ROM.
    """

    tree_offset = rom.convert_to_offset(tree_offset)
    root_offset = rom.convert_to_offset(root_offset)

    root_node = rom.u32(root_offset)

    # this assumes root_node is not a leaf (reasonable, I think)
    max_node_idx = max(root_node & 0xFFFF, (root_node >> 16) & 0xFFFF)

    result_tree = []

    while len(result_tree) <= max_node_idx:
        current_node = rom.u32(tree_offset + 4 * len(result_tree))

        # is node
        if current_node & 0x80000000 == 0:
            max_node_idx = max(max_node_idx, node_next_idx(current_node, 0), node_next_idx(current_node, 1))

        result_tree.append(current_node)

    # last node is root node (always)
    result_tree.append(root_node)

    return result_tree

def decode_atoms(rom : Rom, offset : int, huff_tree : list[int], leaf_mark : int = 0xFFFF0000) -> Iterator[int]:
    offset = rom.convert_to_offset(offset)

    root_node = huff_tree[-1]

    byte = 0
    bits = 0

    while True:
        node = root_node

        # while node isn't leaf
        while node & 0x80000000 == 0:
            if bits == 0:
                # read new byte!
                bits = 8
                byte = rom[offset]
                offset = offset + 1

            node = huff_tree[node_next_idx(node, (byte & 1))]

            byte = byte >> 1
            bits = bits - 1

        value = node & ~leaf_mark

        yield value

        if value == 0:
            # reached zero: the end
            break

def build_table(huff_tree : list[int]) -> dict[int, int]:
    result = {}

    # ALGORITHM:
    # begin:
    #   push all lefts until first Leaf
    #   path is all zeroes with length = len(stack)
    # while stack not empty:
    #   node = pop()
    #   if node is leaf:
    #     map node value to path
    #   if node is not leaf:
    #     if came from left:
    #       set last bit of path to 1
    #       push right then lefts until Leaf

    node_stack = [huff_tree[-1]]

    def push_left():
        while (node_stack[-1] & 0x80000000) == 0:
            node_stack.append(huff_tree[node_next_idx(node_stack[-1], 0)])

    push_left()

    current_path = 0

    while len(node_stack) > 0:
        node = node_stack.pop()

        if (node & 0x80000000) != 0:
            result[node & 0xFFFF] = (current_path << 8) | len(node_stack)

        else:
            which_bit = (current_path >> len(node_stack)) & 1

            if which_bit == 0:
                # we were on the left now we go right
                current_path |= (1 << len(node_stack))
                node_stack.append(node)
                node_stack.append(huff_tree[node_next_idx(node, 1)])
                push_left()

            else:
                # we were on the right now we pop and clear path
                current_path &= (1 << len(node_stack)) - 1

    return result

def encode_atoms(atoms : Iterable[int], huff_table : dict[int, int]) -> bytes:
    result = bytearray()
    bits = 0

    for atom in atoms:
        if atom not in huff_table:
            print(f"DID NOT FIND: {atom:04X}")

        code_length = huff_table[atom] & 0xFF
        code_bits = (huff_table[atom] >> 8)

        for i in range(code_length):
            if bits == 0:
                result.append(0)
                bits = 8

            out_bit = (code_bits >> i) & 1
            result[-1] |= (out_bit) << (8 - bits)
            bits = bits - 1

    return result

def update_frequency_table(table : dict[int, int], atoms : Iterable[int]):
    for value in atoms:
        table[value] = table[value] + 1 if value in table else 1

def build_tree(freq_table : dict[int, int], all_atoms : Iterable[int], leaf_mark : int = 0xFFFF0000):
    huff_tree = []
    huff_list = [] # (idx, freq) sorted in descending order of freq

    for atom in all_atoms:
        if atom in freq_table:
            freq = freq_table[atom]

            # len(huff_tree) is the index of the next element inserted
            item = (len(huff_tree), freq)
            bisect.insort_left(huff_list, item, key = lambda item: -item[1])

            # 0xFFFF0000 (well, really only the top bit) marks leaf nodes
            huff_tree.append(leaf_mark | atom)

    while len(huff_list) > 1:
        (idx0, freq0) = huff_list.pop()
        (idx1, freq1) = huff_list.pop()

        node = idx0 | (idx1 << 16)
        freq = freq0 + freq1

        # len(huff_tree) is the index of the next element inserted
        item = (len(huff_tree), freq)
        bisect.insort_left(huff_list, item, key = lambda item: -item[1])

        huff_tree.append(node)

    return huff_tree

def all_vanilla_atoms() -> Iterator[int]:
    for i in range(0x100):
        yield i

    for i in range(0x100):
        yield 0x100 | i

    for lo in range(0x100):
        for hi in range(2, 0x100):
            yield (hi << 8) | lo

def atomize_string_vanilla(string_bytes : bytes) -> list[int]:
    # add null-terminator if needed
    if len(string_bytes) == 0 or string_bytes[-1] != 0:
        string_bytes = string_bytes + b'\x00'

    result = []
    offset = 0

    while offset < len(string_bytes):
        match string_bytes[offset]:
            case 0x80:
                result.append(string_bytes[offset])
                offset = offset + 1

                if string_bytes[offset] != 0x81:
                    result.append(string_bytes[offset])
                    offset = offset + 1

            case 0x10:
                result.append(string_bytes[offset])
                result.append(string_bytes[offset + 1] + (string_bytes[offset + 2] << 8))
                offset = offset + 3

            case _:
                if string_bytes[offset] < 0x20 or string_bytes[offset] in b'\x7F#<>':
                    result.append(string_bytes[offset])
                    offset = offset + 1

                # in textencode in fe8_us decomp, this next condition is replaced by a check for 0xE9
                # it turns out that a single 0xE9 (é) is the only character affected by this
                # which is funny, as there's actually a single one in the entire corpus
                # (msg 0xD0E, which features the word 'naiveté')
                elif string_bytes[offset + 1:offset + 3] == b'.\x1F':
                    result.append(string_bytes[offset])
                    offset = offset + 1

                else:
                    result.append(string_bytes[offset] + (string_bytes[offset + 1] << 8))
                    offset = offset + 2

    return result

def stringify_atoms_vanilla(atoms : Iterable[int]) -> bytes:
    result = bytearray()

    for atom in atoms:
        result.append(atom & 0xFF)

        if (atom & 0xFF00) != 0:
            result.append((atom & 0xFF00) >> 8)

    return bytes(result)

def decode_string(rom : Rom, offset : int, huff_tree : list[int]) -> bytes:
    return stringify_atoms_vanilla(decode_atoms(rom, offset, huff_tree))

def encode_string(string_bytes : bytes, huff_table : dict[int, int]) -> bytes:
    return encode_atoms(atomize_string_vanilla(string_bytes), huff_table)

def decode_string_old(rom : Rom, offset : int, huff_tree : list[int]) -> bytes:
    offset = rom.convert_to_offset(offset)

    root_node = huff_tree[-1]

    byte = 0
    bits = 0

    result = bytearray()

    while True:
        node = root_node

        # while node isn't leaf
        while node & 0x80000000 == 0:
            if bits == 0:
                # read new byte!
                bits = 8
                byte = rom[offset]
                offset = offset + 1

            node = huff_tree[node_next_idx(node, (byte & 1))]

            byte = byte >> 1
            bits = bits - 1

        # NOTE: vanilla does & 0xFFFF but like this is the same
        value = node & 0xFFFF

        result.append(value & 0xFF)

        if (value & 0xFF00) != 0:
            result.append((value >> 8) & 0xFF)

        elif (value & 0xFF) == 0:
            # reached zero: the end
            return bytes(result)

def encode_string_old(string_bytes : bytes, huff_table : dict[int, int]) -> bytes:
    result = bytearray()
    bits = 0

    offset = 0

    queue = []

    while len(queue) > 0 or offset < len(string_bytes):
        if len(queue) == 0:
            match string_bytes[offset]:
                case 0x80:
                    queue.append(string_bytes[offset])
                    queue.append(string_bytes[offset + 1])
                    offset = offset + 2

                case 0x10:
                    queue.append(string_bytes[offset])
                    queue.append(string_bytes[offset + 1] + (string_bytes[offset + 2] << 8))
                    offset = offset + 3

                case _:
                    if string_bytes[offset] < 0x20 or string_bytes[offset] in b'\x7F#<>':
                        queue.append(string_bytes[offset])
                        offset = offset + 1

                    else:
                        queue.append(string_bytes[offset] + (string_bytes[offset + 1] << 8))
                        offset = offset + 2

        value = queue.pop(0)

        if value not in huff_table:
            print(f"DID NOT FIND: {value:02X}")

        code_length = huff_table[value] & 0xFF
        code_bits = (huff_table[value] >> 8)

        for i in range(code_length):
            if bits == 0:
                result.append(0)
                bits = 8

            out_bit = (code_bits >> i) & 1
            result[-1] |= (out_bit) << (8 - bits)
            bits = bits - 1

    return result
