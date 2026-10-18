"""Diff original vs copy screenshots; print differing row bands and write side-by-side crops."""
import sys
from PIL import Image, ImageChops
tag = sys.argv[1] if len(sys.argv) > 1 else "x"
for n in ['desktop', 'mobile']:
    a = Image.open(f'screenshots/original-{n}.png').convert('RGB'); b = Image.open(f'screenshots/copy-{n}.png').convert('RGB')
    h = min(a.size[1], b.size[1]); w = min(a.size[0], b.size[0])
    d = ImageChops.difference(a.crop((0, 0, w, h)), b.crop((0, 0, w, h))).convert('L').point(lambda x: 255 if x > 40 else 0)
    px = d.load(); bands = []; cur = None
    for y in range(h):
        cnt = sum(1 for x in range(0, w, 2) if px[x, y])
        if cnt > 3:
            if cur and y - cur[1] <= 10: cur[1] = y; cur[2] += cnt
            else:
                if cur: bands.append(cur)
                cur = [y, y, cnt]
    if cur: bands.append(cur)
    bands = [x for x in bands if x[2] > 50]
    print(n, a.size, b.size, bands)
    for i, (s, e, c) in enumerate(bands[:6]):
        s = max(0, s - 30); e = min(h, e + 30)
        A = a.crop((0, s, w, e)); B = b.crop((0, s, w, e))
        out = Image.new('RGB', (w * 2 + 10, e - s), 'red'); out.paste(A, (0, 0)); out.paste(B, (w + 10, 0))
        out.save(f'/tmp/cmp_{tag}_{n}_{i}.png')
