from pathlib import Path
import csv
import struct
import zlib
from PIL import Image,ImageDraw

root=Path(__file__).resolve().parents[1]/'captures/1943h10111'
source=root/'campanha/observacao_02'
dest=root/'primeiros_objetos'
dest.mkdir(exist_ok=True)
frames=list(range(360,2881,120))
decoder=zlib.decompressobj();pending=b'';size=10251;samples={}
with (source/'ram.zlib').open('rb') as stream:
    for chunk in iter(lambda:stream.read(65536),b''):
        pending+=decoder.decompress(chunk)
        count=len(pending)//size
        for i in range(count):
            record=pending[i*size:(i+1)*size]
            frame=struct.unpack_from('<I',record)[0]
            if frame in frames:samples[frame]=record
        pending=pending[count*size:]
        if samples and max(samples)==max(frames):break
with (dest/'registros_amostras.csv').open('w',newline='') as stream:
    writer=csv.writer(stream);writer.writerow(['quadro','registro','base','codigo','paleta','x','y','bytes_00_1F'])
    for frame,record in samples.items():
        ram=record[4+2055:]
        for slot in range(128):
            data=ram[0x1000+slot*32:0x1020+slot*32]
            code=data[0]+((data[1]&0xe0)<<3)
            writer.writerow([frame,f'{slot:02X}',f'{0xf000+slot*32:04X}',f'{code:03X}',data[1]&15,data[3]-(256 if data[1]&16 else 0),data[2],data.hex(' ')])
canvas=Image.new('RGB',(6*160,((len(frames)+5)//6)*200));draw=ImageDraw.Draw(canvas)
for i,frame in enumerate(frames):
    with Image.open(source/f'f{frame:07d}.png') as image:
        image.thumbnail((154,176));x=i%6*160;y=i//6*200
        canvas.paste(image,(x,y));draw.text((x,y+178),str(frame))
canvas.save(dest/'inicio.png')
print(dest)
