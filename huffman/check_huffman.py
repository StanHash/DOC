import sys

from collections.abc import Iterator

from rom import Rom
import huffman as huff

def decode_all_atoms(rom : Rom, message_table_offset : int, huff_tree : list[int]) -> Iterator[bytes]:
    for i in range(0x10000): # 0x12CA * 3 for fe7_eu
        string_offset = rom.u32(message_table_offset + i * 4)

        if (string_offset & 0xFF000000) != 0x08000000:
            break

        yield [atom for atom in huff.decode_atoms(rom, string_offset, huff_tree)]

def print_tree_atoms(f, tree, freq):
    table = huff.build_table(tree)

    for k in sorted(table.keys()):
        bits = table[k] >> 8
        size = table[k] & 0xFF
        f.write(f"{k:04X}: {size:2} {bits:024b} {freq[k] if k in freq else '0'}\n")

def print_tree(f, huff_tree):
    for i, node in enumerate(huff_tree):
        if (node & 0x80000000) != 0:
            f.write(f"LEAF {i:04X}: {node & 0xFFFF:04x}\n")
        else:
            f.write(f"NODE {i:04X}: {node & 0xFFFF:04X} {(node >> 16) & 0xFFFF:04X}\n")

def print_atomized_corpus(f, atomized_corpus):
    for i, atoms in enumerate(atomized_corpus):
        f.write(f"MSG {i:04X}: {' '.join(f'{atom:04X}' for atom in atoms)}\n")

def get_bad_reatomized_matches(atomized_corpus, reatomized_corpus):
    bad_matches = []

    for i, (base, new) in enumerate(zip(atomized_corpus, reatomized_corpus)):
        if base != new:
            bad_matches.append(i)

    return bad_matches

def check_huffman(rom : Rom, freq_adjust : dict[int, int]) -> str:
    decode_string_func_offset = rom.find(b'\xf0\x00\x2d\xe9\x03\x30\x43\xe0')

    if decode_string_func_offset < 0:
        return "Couldn't find the DecodeString function head"

    tree_root_addr = rom.u32(decode_string_func_offset - 8)
    tree_base_addr = rom.u32(decode_string_func_offset - 4)
    message_table_addr = tree_root_addr + 4

    decoded_huff_tree = huff.decode_tree(rom, tree_base_addr, rom.u32(tree_root_addr))

    atomized_corpus = [atoms for atoms in decode_all_atoms(rom, message_table_addr, decoded_huff_tree)]
    corpus = [huff.stringify_atoms_vanilla(atoms) for atoms in atomized_corpus]
    reatomized_corpus = [huff.atomize_string_vanilla(msg) for msg in corpus]

    atomized_bad_matches = get_bad_reatomized_matches(atomized_corpus, reatomized_corpus)

    if len(atomized_bad_matches) > 0:
        with open("atomized_corpus.txt", "w") as f:
            print_atomized_corpus(f, atomized_corpus)

        with open("reatomized_corpus.txt", "w") as f:
            print_atomized_corpus(f, reatomized_corpus)

        return f"Some strings did not reatomize correctly: {', '.join(f'{i:04X}' for i in atomized_bad_matches)}"

    base_freq_table = {}

    for atoms in atomized_corpus:
        huff.update_frequency_table(base_freq_table, atoms)

    freq_table = {}

    for atoms in reatomized_corpus:
        huff.update_frequency_table(freq_table, atoms)

    for atom in freq_adjust:
        if atom in freq_table:
            freq_table[atom] = freq_table[atom] + freq_adjust[atom]

    new_huff_tree = huff.build_tree(freq_table, huff.all_vanilla_atoms())

    if new_huff_tree != decoded_huff_tree:
        with open("decoded_atoms.txt", "w") as f:
            print_tree_atoms(f, decoded_huff_tree, base_freq_table)

        with open("decoded_tree.txt", "w") as f:
            print_tree(f, decoded_huff_tree)

        with open("rebuilt_atoms.txt", "w") as f:
            print_tree_atoms(f, new_huff_tree, freq_table)

        with open("rebuilt_tree.txt", "w") as f:
            print_tree(f, new_huff_tree)

        with open("atomized_corpus.txt", "w") as f:
            print_atomized_corpus(f, atomized_corpus)

        return "Failed to generate matching tree"

    huff_table = huff.build_table(new_huff_tree)

    bad_matches = []

    for i, atoms in enumerate(reatomized_corpus):
        base_offset = rom.u32(message_table_addr + i * 4)
        reencoded = huff.encode_atoms(atoms, huff_table)

        if not rom.bytes_equal(base_offset, reencoded):
            bad_matches.append(i)

    if len(bad_matches) > 0:
        return f"Some strings did not match: {', '.join(bad_matches)}"

    return "OK"

FREQ_ADJUST_FE7_JP = { 0xB388: -1, 0xA790: -1 }
FREQ_ADJUST_FE8_JP = { 0xDD82: -1 }

def main(args):
    for rom_path in args[1:]:
        with open(rom_path, "rb") as f:
            rom = Rom(f.read())

        freq_adjust = {}

        if rom.bytes_equal(0xA0, b'FIREEMBLEM7\x00AE7J'):
            freq_adjust = FREQ_ADJUST_FE7_JP

        if rom.bytes_equal(0xA0, b'FIREEMBLEM8\x00BE8J'):
            freq_adjust = FREQ_ADJUST_FE8_JP

        print(f"{rom_path}: {check_huffman(rom, freq_adjust)}")

if __name__ == '__main__':
    sys.exit(main(sys.argv))
