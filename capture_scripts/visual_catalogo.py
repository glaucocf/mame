"""Referencias visuais com o layout exato do driver MAME; nao edita imagens."""
from pathlib import Path
from PIL import Image,ImageDraw,ImageFont
import csv,sys,zipfile

base=Path(__file__).resolve().parents[1]
rom=sys.argv[1]
dest=base/'captures'/rom/'catalogacao_01'/'analise'
dest.mkdir(exist_ok=True)
with zipfile.ZipFile(base/'roms'/f'{rom}.zip') as archive:
    gfx=b''.join(archive.read(name) for name in ['06.10a','07.11a','08.12a','09.14a','10.10c','11.11c','12.12c','13.14c'])
    def member(name):
        if name in archive.namelist():return archive.read(name)
        for prefix in ['bm','bmk']:
            if prefix+name in archive.namelist():return archive.read(prefix+name)
        raise KeyError(name)
    proms=b''.join(member(name) for name in ['1.12a','2.13a','3.14a','5.7f','10.7l','9.6l','12.12m','11.12l','8.8c','7.7c','4.12c','6.4b'])
half=len(gfx)*4
planes=[half+4,half,4,0]
xoffs=[*range(4),*range(8,12),*range(256,260),*range(264,268)]
def tile(code,palette=None):
    pixels=[]
    for y in range(16):
        for x in range(16):
            value=0
            for p,offset in enumerate(planes):
                bit=code*512+offset+xoffs[x]+y*16
                value|=((gfx[bit//8]>>(7-bit%8))&1)<<(3-p)
            if palette is None:color=(value*17,)*3+(255,)
            else:
                i=palette*16+value
                hw=0x80|((proms[0x900+i]&7)<<4)|(proms[0x800+i]&15)
                rgb=[]
                for channel in range(3):
                    n=proms[channel*256+hw]
                    rgb.append(sum(w*((n>>b)&1) for b,w in enumerate([14,31,67,143])))
                color=tuple(rgb)+(255 if value else 0,)
            pixels.append(color)
    result=Image.new('RGBA',(16,16));result.putdata(pixels)
    return result.transpose(Image.Transpose.ROTATE_90)

items=Image.new('RGB',(12*84,12*88),(30,30,35));idraw=ImageDraw.Draw(items)
for i,code in enumerate(range(0x90,0x120)):
    x=(i%12)*84;y=(i//12)*88
    t=tile(code,9).resize((64,64),Image.Resampling.NEAREST)
    items.paste(t,(x,y),t);idraw.text((x+12,y+65),f'{code:03X} p9',fill='white')
items.save(dest/'itens_referencia.png')
cats=Image.new('RGB',(4*180,200),(30,30,35));cdraw=ImageDraw.Draw(cats)
for i,code in enumerate([0x5c4,0x5c5,0x5cc,0x5cd]):
    t=tile(code,9).resize((160,160),Image.Resampling.NEAREST)
    cats.paste(t,(i*180,0),t);cdraw.text((i*180+40,170),f'{code:03X} p9',fill='white')
cats.save(dest/'gatinho_candidato_graficos.png')

# Paginas monocromaticas permitem reconhecer tambem itens raros sem adivinhar a paleta.
for page in range(8):
    sheet=Image.new('RGB',(16*60,16*68),(30,30,35));draw=ImageDraw.Draw(sheet)
    for index in range(256):
        code=page*256+index;x=(index%16)*60;y=(index//16)*68
        sheet.paste(tile(code).resize((48,48),Image.Resampling.NEAREST),(x,y))
        draw.text((x+10,y+49),f'{code:03X}',fill='white')
    sheet.save(dest/f'sprites_{page:01X}00_{page:01X}FF.png')

rows=list(csv.DictReader((dest/'modelos.csv').open(encoding='utf-8-sig')))
for page in range((len(rows)+19)//20):
    selected=rows[page*20:(page+1)*20]
    sheet=Image.new('RGB',(1100,len(selected)*88),(25,29,35));draw=ImageDraw.Draw(sheet)
    for index,row in enumerate(selected):
        y=index*88
        draw.text((8,y+4),f"{row['modelo']}  b{row['banco']}:{row['modelo_ROM']} ref {row['referencia_1C']} f{row['primeiro_quadro']} fase {row['fases']}",fill='white')
        draw.text((8,y+21),row['rotulo'],fill=(170,205,255))
        for j,item in enumerate(row['graficos_paletas_observados'].split()[:12]):
            code,pal=item.split('/p');x=410+j*55
            t=tile(int(code,16),int(pal,16)).resize((48,48),Image.Resampling.NEAREST)
            sheet.paste(t,(x,y+2),t);draw.text((x,y+54),item,fill='white')
    sheet.save(dest/f'modelos_{page+1:02d}.png')
print(rom,len(rows),'modelos; atlas e referencias visuais gerados',flush=True)

if len(sys.argv)>2 and sys.argv[2]=='--match':
    picture=Image.open(sys.argv[3]).convert('RGB');code=int(sys.argv[4],16);pal=int(sys.argv[5],16)
    for angle in [0,90,180,270]:
        t=tile(code,pal).rotate(angle)
        visible=[(x,y,t.getpixel((x,y))[:3]) for y in range(16) for x in range(16) if t.getpixel((x,y))[3]]
        anchor=visible[0]
        matches=[]
        pix=picture.load()
        for y in range(picture.height-15):
            for x in range(picture.width-15):
                if pix[x+anchor[0],y+anchor[1]]==anchor[2] and all(pix[x+dx,y+dy]==color for dx,dy,color in visible):matches.append((x,y))
        print('rotacao extra',angle,'correspondencias',matches,flush=True)
