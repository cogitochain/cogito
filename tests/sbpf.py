import struct

M64 = (1 << 64) - 1
RO = 0x0
TEXT = 0x100000000
HEAP = 0x300000000
INPUT = 0x400000000


def sx32(v):
    v &= 0xffffffff
    return v - (1 << 32) if v & 0x80000000 else v


def s64(v):
    v &= M64
    return v - (1 << 64) if v >> 63 else v


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


def run(blob, data, accounts=0, logdata_hash=None, limit=5_000_000):
    _, entry, segs = load_elf(blob)
    ro = next(s for s in segs if s[2] == RO)[3]
    text = next(s for s in segs if s[2] == TEXT)[3]
    ins = decode(text)
    inp = bytearray(struct.pack("<QQ", accounts, len(data)) + bytes(data) + bytes(32))
    mem = Memory([(RO, ro), (HEAP, bytearray(32 * 1024)), (INPUT, inp)])
    r = [0] * 11
    r[1] = INPUT
    pc = (entry - TEXT) // 8
    logged = []
    steps = 0
    while True:
        steps += 1
        if steps > limit:
            raise RuntimeError("instruction limit")
        op, regs, off, imm = ins[pc]
        dst, src = regs & 15, regs >> 4
        pc += 1
        if op == 0x18:
            r[dst] = (imm | (ins[pc][3] << 32)) & M64
            pc += 1
        elif op == 0xb7:
            r[dst] = sx32(imm) & M64
        elif op == 0xbf:
            r[dst] = r[src]
        elif op == 0x07:
            r[dst] = (r[dst] + sx32(imm)) & M64
        elif op == 0x0f:
            r[dst] = (r[dst] + r[src]) & M64
        elif op == 0x2f:
            r[dst] = (r[dst] * r[src]) & M64
        elif op == 0x67:
            r[dst] = (r[dst] << (imm & 63)) & M64
        elif op == 0x77:
            r[dst] = r[dst] >> (imm & 63)
        elif op == 0xc7:
            r[dst] = (s64(r[dst]) >> (imm & 63)) & M64
        elif op == 0x71:
            r[dst] = mem.load((r[src] + off) & M64, 1)
        elif op == 0x79:
            r[dst] = mem.load((r[src] + off) & M64, 8)
        elif op == 0x73:
            mem.store((r[dst] + off) & M64, 1, r[src])
        elif op == 0x63:
            mem.store((r[dst] + off) & M64, 4, r[src])
        elif op == 0x7b:
            mem.store((r[dst] + off) & M64, 8, r[src])
        elif op == 0x05:
            pc += off
        elif op == 0x55:
            if r[dst] != sx32(imm) & M64:
                pc += off
        elif op == 0xa5:
            if r[dst] < sx32(imm) & M64:
                pc += off
        elif op == 0x65:
            if s64(r[dst]) > sx32(imm):
                pc += off
        elif op == 0x85:
            if imm != logdata_hash:
                raise ValueError("unsupported call 0x%08x" % imm)
            out = b""
            for i in range(r[2]):
                p = mem.load(r[1] + 16 * i, 8)
                n = mem.load(r[1] + 16 * i + 8, 8)
                out += mem.read(p, n)
            logged.append(out)
            r[0] = 0
        elif op == 0x95:
            return r[0], logged, steps
        else:
            raise ValueError("unsupported opcode 0x%02x" % op)
