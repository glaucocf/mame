from pathlib import Path
from PIL import Image,ImageDraw
import sys,hashlib
d=Path(sys.argv[1])
rows=[]
prev=None
for p in sorted(d.glob('f*.png')):
    im=Image.open(p).convert('RGB')
    sig=hashlib.sha1(im.tobytes()).hexdigest()
    if sig!=prev:
        rows.append((p,im))
    prev=sig
print("mudancas",len(rows),[p.name for p,im in rows[:100]])
if len(rows)>45:rows=rows[:30]+rows[30::max(1,(len(rows)-30)//12)]
out=Image.new('RGB',(6*132,((len(rows)+5)//6)*144))
dr=ImageDraw.Draw(out)
for j,(p,im) in enumerate(rows):
    im.thumbnail((125,124));x=j%6*132;y=j//6*144
    out.paste(im,(x,y));dr.text((x,y+124),p.stem)
out.save(d/'transicoes.png')
