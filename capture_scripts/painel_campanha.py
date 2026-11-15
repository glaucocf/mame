from pathlib import Path
import csv
from PIL import Image, ImageDraw

root=Path(__file__).resolve().parents[1]/'captures'
rom='1943h10111'
folder=root/rom/'campanha'/'campanha_com_tiro_01'
rows=list(csv.DictReader((folder/'eventos.csv').read_text().splitlines()))
transitions=[int(r['quadro']) for r in rows if r['evento']=='fase' and int(r['quadro'])>400]
frames=[]
for frame in transitions[:2]:
    frames.extend(range((frame-1800)//120*120,(frame+1800)//120*120+1,120))
canvas=Image.new('RGB',(8*120,((len(frames)+7)//8)*156))
draw=ImageDraw.Draw(canvas)
for index,frame in enumerate(frames):
    path=folder/f'f{frame:07d}.png'
    if not path.exists():continue
    with Image.open(path) as image:
        image.thumbnail((112,128));x=index%8*120;y=index//8*156
        canvas.paste(image,(x,y));draw.text((x,y+130),str(frame))
canvas.save(folder/'transicoes_iniciais.png')
