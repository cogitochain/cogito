import numpy as np
from PIL import Image

N = 16


def to_input(ink, box=12, shift=(0, 0)):
    ink = np.asarray(ink, dtype=np.float32)
    ys, xs = np.nonzero(ink > 0.02)
    if len(ys) == 0:
        return np.zeros(N * N, dtype=np.uint8)
    crop = ink[ys.min():ys.max() + 1, xs.min():xs.max() + 1]
    h, w = crop.shape
    s = box / max(h, w)
    nh, nw = max(1, round(h * s)), max(1, round(w * s))
    img = Image.fromarray((np.clip(crop, 0, 1) * 255).astype(np.uint8)).resize((nw, nh), Image.BOX)
    small = np.asarray(img, dtype=np.float32) / 255.0
    tot = small.sum()
    if tot <= 0:
        return np.zeros(N * N, dtype=np.uint8)
    cy = (small.sum(1) * np.arange(nh)).sum() / tot
    cx = (small.sum(0) * np.arange(nw)).sum() / tot
    oy = int(round(7.5 - cy)) + shift[0]
    ox = int(round(7.5 - cx)) + shift[1]
    out = np.zeros((N, N), dtype=np.float32)
    r0, c0 = max(0, -oy), max(0, -ox)
    r1, c1 = min(nh, N - oy), min(nw, N - ox)
    if r1 > r0 and c1 > c0:
        out[r0 + oy:r1 + oy, c0 + ox:c1 + ox] = small[r0:r1, c0:c1]
    return np.round(out * 255).astype(np.uint8).reshape(-1)
