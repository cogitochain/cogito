import hashlib
import sys

MAGIC = b"COGMIND1"
IN, HIDDEN, OUT = 256, 128, 16
SIZE = len(MAGIC) + HIDDEN * IN + OUT * HIDDEN
