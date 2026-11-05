import struct

RO = 0x0
TEXT = 0x100000000


def load_elf(blob):
    assert blob[:4] == b"\x7fELF"
    machine, = struct.unpack_from("<H", blob, 18)
    entry, phoff = struct.unpack_from("<QQ", blob, 24)
    phnum, = struct.unpack_from("<H", blob, 56)
    segs = []
    for i in range(phnum):
        p_type, p_flags, off, vaddr, _, filesz, _, _ = struct.unpack_from("<IIQQQQQQ", blob, phoff + 56 * i)
        segs.append((p_type, p_flags, vaddr, blob[off:off + filesz]))
    return machine, entry, segs


def decode(text):
    return [struct.unpack_from("<BBhI", text, i) for i in range(0, len(text), 8)]


class Memory:
    def __init__(self, regions):
        self.regions = regions

    def _find(self, addr, n):
        for base, buf in self.regions:
            if base <= addr and addr + n <= base + len(buf):
                return buf, addr - base
        raise IndexError("access outside mapped memory: 0x%x" % addr)

    def load(self, addr, n):
        buf, o = self._find(addr, n)
        return int.from_bytes(bytes(buf[o:o + n]), "little")

    def read(self, addr, n):
        buf, o = self._find(addr, n)
        return bytes(buf[o:o + n])

    def store(self, addr, n, v):
        buf, o = self._find(addr, n)
        if not isinstance(buf, bytearray):
            raise IndexError("write to read-only memory: 0x%x" % addr)
        buf[o:o + n] = (v & ((1 << (8 * n)) - 1)).to_bytes(n, "little")
