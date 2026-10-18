import sys,glob,os
from PIL import Image
pre=sys.argv[1]; tag=sys.argv[2]
[os.remove(f) for f in glob.glob(f'/tmp/{tag}_*')]
for n in ['desktop','mobile']:
  im=Image.open(f'{pre}-{n}.png'); w,h=im.size; step=1400
  for i,y in enumerate(range(0,h,step)):
    c=im.crop((0,y,w,min(h,y+step)))
    if n=='desktop': c=c.resize((w*3//4,c.size[1]*3//4))
    c.save(f'/tmp/{tag}_{n}_{i}.png')
print(sorted(glob.glob(f'/tmp/{tag}_*')))
