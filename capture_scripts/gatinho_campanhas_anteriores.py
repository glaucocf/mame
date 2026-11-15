from pathlib import Path
import zlib,struct,json,sys
base=Path(__file__).resolve().parents[1]
rom=sys.argv[1];folder=base/'captures'/rom/'campanha'/'campanha_com_tiro_01'
decoder=zlib.decompressobj();pending=b'';periods=[];active={};last=0
screens=[]
ram_start=4+2055;sprite_start=ram_start+0x1000
with (folder/'ram.zlib').open('rb') as stream:
    while chunk:=stream.read(65536):
        pending+=decoder.decompress(chunk);size=len(pending)//10251*10251
        for off in range(0,size,10251):
            frame=struct.unpack_from('<I',pending,off)[0];last=frame
            seen=set()
            for slot in range(128):
                p=off+sprite_start+slot*32
                code,attr,y,x=pending[p:p+4]
                if code in (0xc4,0xc5,0xcc,0xcd) and attr==0xa9 and 16<=y<240:
                    seen.add(slot)
                    if frame%4==0:screens.append((frame,code+0x500,x,y))
                    if slot not in active:
                        item={'primeiro_quadro':frame,'ultimo_quadro':frame,'registro':f'{slot:02X}','fase_id':pending[off+ram_start+0x450],'x':x,'y':y,'arma':f'{pending[off+ram_start+0x1251]:02X}'}
                        periods.append(item);active[slot]=item
                    active[slot]['ultimo_quadro']=frame
                    if frame in (163100,299300,299500):active[slot].setdefault('amostras',[]).append({'quadro':frame,'codigo':f'{code:03X}','x':x,'y':y,'registro_hex':pending[p:p+32].hex()})
            active={slot:value for slot,value in active.items() if slot in seen}
        pending=pending[size:]
assert decoder.eof and not pending
result={'rom':rom,'quadros':last,'ocorrencias_grafico_gatinho':periods}
if len(sys.argv)>2 and sys.argv[2]=='--visual':
    import visual_catalogo as gfx
    from PIL import Image
    best=(0,None)
    for frame,code,x,y in screens:
        path=folder/f'f{frame:07d}.png'
        if not path.exists():continue
        picture=Image.open(path).convert('RGB');pixels=picture.load();t=gfx.tile(code,9)
        visible=[(dx,dy,t.getpixel((dx,dy))[:3]) for dy in range(16) for dx in range(16) if t.getpixel((dx,dy))[3]]
        for ax in range(y-18,y-13):
            for ay in range(238-x,243-x):
                if ax<0 or ay<0 or ax+16>picture.width or ay+16>picture.height:continue
                score=sum(pixels[ax+dx,ay+dy]==color for dx,dy,color in visible)/len(visible)
                if score>best[0]:best=(score,{'quadro':frame,'codigo':f'{code:03X}','imagem':str(path),'x_imagem':ax,'y_imagem':ay})
        if best[0]==1:break
    result['confirmacao_visual']={'fracao_pixels_iguais':best[0],'amostra':best[1]}
(base/'captures'/rom/'catalogacao_01'/'analise'/'gatinho_campanha_anterior.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
print(json.dumps(result,indent=2),flush=True)
