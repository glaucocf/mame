from pathlib import Path
from collections import Counter
import struct,zlib,json
from captura_armas_gif import ROMS,WEAPONS
base=Path(__file__).resolve().parents[1];root=base/'captures'/'gifs_armas_01'
result=[]
for rom,weapons in ROMS.items():
    for weapon in weapons:
        folder=root/'registros'/rom/f'{weapon:02X}_{WEAPONS[weapon]}'
        data=zlib.decompress((folder/'dma.zlib').read_bytes())
        strengths=Counter();initial=Counter();drops=[];previous={}
        for off in range(0,len(data),4101):
            frame=struct.unpack_from('<I',data,off)[0];raw=data[off+5:off+4101]
            for slot in range(0x1c,0x2e):
                r=raw[slot*32:slot*32+32];old=previous.get(slot)
                if r[8]==2:
                    strengths[r[13]]+=1
                    if old is None or old[8]!=2:initial[r[13]]+=1
                    if old is not None and old[8]==2 and 0<r[13]<old[13]:
                        drops.append({'quadro':frame,'registro':f'{slot:02X}','forca_antes':old[13],'forca_depois':r[13],'codigo':f'{r[0]+((r[1]&0xe0)<<3):03X}'})
                previous[slot]=r
        result.append({'rom':rom,'arma':f'{weapon:02X}','campo_0D_enquanto_estado_02':dict(strengths),'campo_0D_entrada_estado_02':dict(initial),'reducoes_positivas':drops[:20],'total_reducoes_positivas':len(drops)})
(root/'forca_tiros_observada.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
for item in result:
    print(item['rom'],item['arma'],'entrada',item['campo_0D_entrada_estado_02'],'observados',item['campo_0D_enquanto_estado_02'],'reducoes',item['total_reducoes_positivas'],item['reducoes_positivas'][:3],flush=True)
