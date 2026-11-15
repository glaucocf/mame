from pathlib import Path
import struct,zlib,json
base=Path(__file__).resolve().parents[1];root=base/'captures'/'gifs_armas_01';result=[]
for rom,values in [('1943h10111',[16]),('1943h11000',[16,48,80])]:
    for weapon in values:
        names={16:'laser',48:'laser_plus',80:'laser_supremo'}
        data=zlib.decompress((root/'registros'/rom/f'{weapon:02X}_{names[weapon]}'/'dma.zlib').read_bytes())
        for off in range(0,len(data),4101):
            frame=struct.unpack_from('<I',data,off)[0];raw=data[off+5:off+4101]
            parts=[]
            for slot in range(0x1c,0x2e):
                r=raw[slot*32:slot*32+32];code=r[0]+((r[1]&0xe0)<<3)
                if r[8]==2 and code in (0x96,0x9f):
                    x=r[3]-((r[1]&16)<<4)
                    parts.append({'slot':f'{slot:02X}','endereco':f'{0xf000+slot*32:04X}','codigo':f'{code:03X}','forca':r[13],'x_imagem':r[2]-16,'y_imagem':240-x,'raw':r.hex()})
            if len(parts)==(3 if rom=='1943h10111'else 2) and len({p['y_imagem']for p in parts})==len(parts):
                parts.sort(key=lambda row:row['y_imagem'])
                result.append({'rom':rom,'arma':f'{weapon:02X}','quadro':frame,'partes_de_cima_para_baixo':parts});break
data=zlib.decompress((root/'registros'/'1943h10111'/'10_laser'/'dma.zlib').read_bytes())
independent=None
for off in range(0,len(data),4101):
    frame=struct.unpack_from('<I',data,off)[0]
    if not 35<=frame<=60:continue
    raw=data[off+5:off+4101];parts=[raw[s*32:s*32+32]for s in [0x1c,0x1d,0x1e]]
    if all(r[8]==2 and r[0]==0x96 for r in parts)and len({r[13]for r in parts})>1:
        independent={'quadro':frame,'forcas_nos_registros_1C_1D_1E':[r[13]for r in parts]};break
(root/'independencia_laser_1943.json').write_text(json.dumps(independent,indent=2),encoding='utf-8')
(root/'segmentos_laser.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
print('Exemplo de forcas independentes:',json.dumps(independent),flush=True)
print(json.dumps(result,indent=2),flush=True)
