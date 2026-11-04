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
