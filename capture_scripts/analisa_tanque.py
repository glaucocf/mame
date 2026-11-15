from pathlib import Path
import csv
import struct
import zlib

root=Path(__file__).resolve().parents[1]/'captures'
size=10251
out=[]
for rom,end in [('1943h10111',161530),('1943h00111',166731),('1943h11000',290271)]:
    path=root/rom/'campanha'/'campanha_com_tiro_01'/'ram.zlib'
    decoder=zlib.decompressobj();pending=b'';previous=None
    with path.open('rb') as stream:
        for chunk in iter(lambda:stream.read(65536),b''):
            pending+=decoder.decompress(chunk)
            count=len(pending)//size
            for i in range(count):
                offset=i*size;frame=struct.unpack_from('<I',pending,offset)[0]
                if frame>=end:break
                tank=pending[offset+4+2055+0x12f]
                if tank!=previous:
                    stage=pending[offset+4+2055+0x450]
                    energy=pending[offset+4+2055+0x1206]
                    out.append([rom,frame,stage+1,previous,tank,energy])
                    previous=tank
            if frame>=end:break
            pending=pending[count*size:]
with (root/'tanque_alteracoes.csv').open('w',encoding='utf-8-sig',newline='') as stream:
    writer=csv.writer(stream);writer.writerow(['ROM','quadro','fase_1_a_16','tanque_anterior','tanque_atual','energia_atual']);writer.writerows(out)
for row in out:print(*row)
