"""Side-by-side review sheet: one row per frame, reference first, then each test version.

python compare_frames.py cmp.jpg --frames 300,1350 --ref 'ref/ref_{}.png' --test 'v3/f_{}.png' --test 'v4/f_{}.png'
"""
import argparse
from PIL import Image

p = argparse.ArgumentParser()
p.add_argument('out')
p.add_argument('--frames', required=True)
p.add_argument('--ref', required=True)
p.add_argument('--test', action='append', required=True)
p.add_argument('--width', type=int, default=640)
a = p.parse_args()
frames = [int(x) for x in a.frames.split(',')]
paths = [a.ref] + a.test
first = Image.open(paths[0].format(frames[0]))
W = a.width; H = round(W * first.height / first.width)
sheet = Image.new('RGB', (W * len(paths), H * len(frames)))
for row, f in enumerate(frames):
    for col, path in enumerate(paths):
        sheet.paste(Image.open(path.format(f)).convert('RGB').resize((W, H), Image.LANCZOS), (col * W, row * H))
sheet.save(a.out, quality=90)
print('saved', a.out, sheet.size)
