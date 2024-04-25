
class Rom(bytearray):
    def __init__(self, rom_bytes : bytes):
        self[:] = rom_bytes

    def convert_to_offset(self, maybe_address : int) -> int:
        if maybe_address >= 0x08000000 and maybe_address < 0x08000000 + len(self):
            return maybe_address - 0x08000000

        return maybe_address

    def u32(self, offset : int) -> int:
        offset = self.convert_to_offset(offset)
        return int.from_bytes(self[offset:offset + 4], 'little')

    def u16(self, offset : int) -> int:
        offset = self.convert_to_offset(offset)
        return int.from_bytes(self[offset:offset + 2], 'little')

    def bytes_equal(self, offset : int, to_compare : bytes):
        offset = self.convert_to_offset(offset)

        beg = offset
        end = min(offset + len(to_compare), len(self))

        view = memoryview(self)
        return view[beg:end] == memoryview(to_compare)
