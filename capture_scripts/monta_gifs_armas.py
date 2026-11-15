from pathlib import Path
from functools import lru_cache
from bisect import bisect_right
from PIL import Image,ImageDraw,ImageFont,ImageSequence
import csv,json,struct,zipfile,zlib,sys
from captura_armas_gif import WEAPONS,ROMS

base=Path(__file__).resolve().parents[1];root=base/'captures'/'gifs_armas_01'
NAMES={0:'Normal',1:'Auto',2:'Shot Gun',3:'Shot Gun +',4:'Three Way',8:'Shell',0x10:'Laser',0x30:'Laser +',0x50:'Laser supremo'}
FONT=ImageFont.truetype('C:/Windows/Fonts/arial.ttf',18)
SMALL=ImageFont.truetype('C:/Windows/Fonts/arial.ttf',15)

class Sprites:
    def __init__(self,rom):
        with zipfile.ZipFile(base/'roms'/f'{rom}.zip') as archive:
            def member(name):
                for prefix in ['', 'bm','bmk']:
                    if prefix+name in archive.namelist():return archive.read(prefix+name)
                raise KeyError(name)
            self.gfx=b''.join(member(n) for n in ['06.10a','07.11a','08.12a','09.14a','10.10c','11.11c','12.12c','13.14c'])
            self.proms=b''.join(member(n) for n in ['1.12a','2.13a','3.14a','5.7f','10.7l','9.6l','12.12m','11.12l','8.8c','7.7c','4.12c','6.4b'])
    @lru_cache(maxsize=None)
    def tile(self,code,pal):
        gfx=self.gfx;proms=self.proms;half=len(gfx)*4;planes=[half+4,half,4,0]
        xoffs=[*range(4),*range(8,12),*range(256,260),*range(264,268)]
        pixels=[]
        for y in range(16):
            for x in range(16):
                value=0
                for p,offset in enumerate(planes):
                    bit=code*512+offset+xoffs[x]+y*16
                    value|=((gfx[bit//8]>>(7-bit%8))&1)<<(3-p)
                i=pal*16+value;hw=0x80|((proms[0x900+i]&7)<<4)|(proms[0x800+i]&15)
                rgb=tuple(sum(w*((proms[c*256+hw]>>b)&1) for b,w in enumerate([14,31,67,143])) for c in range(3))
                pixels.append(rgb+(255 if value else 0,))
        t=Image.new('RGBA',(16,16));t.putdata(pixels);return t
    def render(self,raw,control=0,slots=range(0x10,0x2e),mask=False):
        canvas=Image.new('RGB',(256,256),'black');alpha=Image.new('L',(256,256),0)
        # O driver marca o primeiro pixel de sprite desenhado como ocupado.
        # Pintar os registros em ordem inversa reproduz essa prioridade.
        for slot in reversed(tuple(slots)):
            low,attr,y,x=raw[slot*32:slot*32+4]
            x-=((attr&16)<<4);code=low+((attr&0xe0)<<3)
            t=self.tile(code,attr&15)
            if control&0x40:x=240-x;y=240-y;t=t.transpose(Image.Transpose.ROTATE_180)
            canvas.paste(t,(x,y),t);alpha.paste(t.getchannel('A'),(x,y),t.getchannel('A'))
        crop=(0,16,256,240)
        result=canvas.crop(crop).transpose(Image.Transpose.ROTATE_90)
        return (result,alpha.crop(crop).transpose(Image.Transpose.ROTATE_90)) if mask else result

def load_run(rom,weapon):
    folder=root/'registros'/rom/f'{weapon:02X}_{WEAPONS[weapon]}'
    status=dict(line.split('=',1) for line in (folder/'status.txt').read_text().splitlines())
    assert status['resultado']=='ok' and int(status['quadros'])==420
    decoder=zlib.decompressobj();data=decoder.decompress((folder/'dma.zlib').read_bytes())+decoder.flush()
    assert decoder.eof and len(data)%4101==0
    records=[]
    for off in range(0,len(data),4101):
        n,control=struct.unpack_from('<IB',data,off);records.append((n,control,data[off+5:off+4101]))
    assert len(records)==int(status['dma']) and all(records[i][0]<=records[i+1][0] for i in range(len(records)-1))
    log=list(csv.DictReader((folder/'quadros.csv').open()))
    assert len(log)==420 and [int(r['quadro']) for r in log]==list(range(1,421))
    assert all(int(r['arma_forcada'],16)==weapon for r in log)
    times=dict(line.split('=',1) for line in (folder/'video.txt').read_text().splitlines())
    frames=[r[0] for r in records];sprites=Sprites(rom)
    images=[]
    for n in range(2,421,2):
        idx=max(0,bisect_right(frames,n-1)-1);_,control,raw=records[idx]
        images.append(sprites.render(raw,control))
    # Correspondencia com screenshots reais. Pode haver um quadro entre CPU/DMA e a imagem.
    checks=[]
    for n in [60,120,200,240,330]:
        actual=Image.open(folder/f'mame_f{n:04d}.png').convert('RGB');best=0;best_full=0
        for delta in [-2,-1,0,1]:
            idx=max(0,bisect_right(frames,n+delta)-1)
            _,control,raw=records[idx];render,mask=sprites.render(raw,control,mask=True)
            a=list(actual.get_flattened_data());b=list(render.get_flattened_data());m=list(mask.get_flattened_data())
            count=sum(v>0 for v in m)
            score=sum(x==y for x,y,v in zip(a,b,m) if v>0)/max(count,1)
            best=max(best,score)
            full=sprites.render(raw,control,slots=range(128))
            full_score=sum(x==y for x,y in zip(a,full.get_flattened_data()))/len(a)
            best_full=max(best_full,full_score)
        assert best_full==1.0,(rom,weapon,n,best_full)
        checks.append({'quadro':n,'fracao_pixels_jogador_iguais':round(best,6),'fracao_tela_completa_sprites_igual':best_full})
    images[59].save(folder/'jogador_isolado_f0120.png')
    return images,float(times['frame_period'].replace(',','.')),checks

def phase(n):
    if n<=30:return 'Botao solto'
    if n<=150:return 'Botao mantido pressionado'
    if n<=180:return 'Botao solto'
    if n<=300:return 'Toques repetidos: 3 quadros ligado / 3 solto'
    return 'Botao solto: trajetoria final dos tiros'

def panel(rom,weapon,frame,n):
    image=Image.new('RGB',(448,590),(0,0,0));d=ImageDraw.Draw(image);d.fontmode='1'
    title='1943 - engine 1943' if rom=='1943h10111' else 'Kai - engine Kai'
    art='1943h10111 | arte dos sprites: Kai' if rom=='1943h10111' else '1943h11000 | arte dos sprites: 1943'
    d.text((10,8),title,fill='white',font=FONT);d.text((10,31),art,fill=(170,195,220),font=SMALL)
    image.paste(frame.resize((448,512),Image.Resampling.NEAREST),(0,58))
    if rom=='1943h11000' and weapon in (1,2):d.text((10,548),'Arma ativada por cheat no Kai',fill=(255,200,70),font=SMALL)
    if weapon==0x10:d.text((10,548),'Laser supremo' if rom=='1943h10111' else 'Laser inicial',fill=(255,200,70),font=SMALL)
    d.text((10,573),f'Quadro {n:03d}',fill=(170,195,220),font=SMALL)
    return image

def save_gif(path,frames,period):
    colors=set()
    for frame in frames:
        palette=frame.getcolors(256);assert palette is not None,'mais de 256 cores em um quadro'
        colors.update(color for count,color in palette)
    assert len(colors)<=256,('paleta global',len(colors))
    colors=sorted(colors);table=[v for color in colors for v in color];table+=[0]*(768-len(table))
    palette=Image.new('P',(1,1));palette.putpalette(table)
    indexed=[frame.quantize(palette=palette,dither=Image.Dither.NONE) for frame in frames]
    durations=[int(round((i+1)*2*period*100)-round(i*2*period*100))*10 for i in range(len(frames))]
    path.parent.mkdir(parents=True,exist_ok=True)
    indexed[0].save(path,save_all=True,append_images=indexed[1:],duration=durations,loop=0,optimize=False,disposal=2)
    with Image.open(path) as result:
        total=sum(frame.info.get('duration',0) for frame in ImageSequence.Iterator(result))
        assert result.n_frames>1 and total==sum(durations)
        return {'arquivo':str(path),'quadros_gif':result.n_frames,'duracao_ms':total,'cores':len(colors),'tamanho_bytes':path.stat().st_size}

def main():
    pilot='--piloto' in sys.argv or '--piloto-shotgun' in sys.argv
    jobs=[('1943h10111',2 if '--piloto-shotgun' in sys.argv else 0)] if pilot else [(rom,w) for rom,values in ROMS.items() for w in values]
    loaded={};validation=[]
    for rom,weapon in jobs:
        images,period,checks=load_run(rom,weapon);loaded[(rom,weapon)]=(images,period)
        decorated=[]
        for i,frame in enumerate(images):
            n=2*(i+1);body=panel(rom,weapon,frame,n);out=Image.new('RGB',(448,636),(20,25,32));out.paste(body,(0,26))
            d=ImageDraw.Draw(out);d.fontmode='1';d.text((10,3),f'{weapon:02X} - {NAMES[weapon]}',font=FONT,fill='white');d.text((10,616),phase(n),font=SMALL,fill='white');decorated.append(out)
        path=root/rom/f'{weapon:02X}_{WEAPONS[weapon]}.gif'
        info=save_gif(path,decorated,period);info['rom']=rom;info['arma_hex']=f'{weapon:02X}';info['comparacao_com_MAME']=checks;validation.append(info)
        print(rom,f'{weapon:02X}',info['quadros_gif'],info['duracao_ms'],'ms',flush=True)
    if not pilot:
        for weapon in WEAPONS:
            images,period=loaded[('1943h11000',weapon)];frames=[]
            for i,frame in enumerate(images):
                n=(i+1)*2;out=Image.new('RGB',(912,636),(20,25,32));d=ImageDraw.Draw(out);d.fontmode='1'
                d.text((10,3),f'{weapon:02X} - {NAMES[weapon]}',font=FONT,fill='white')
                if ('1943h10111',weapon) in loaded:left=panel('1943h10111',weapon,loaded[('1943h10111',weapon)][0][i],n)
                else:
                    left=Image.new('RGB',(448,590),'black');ld=ImageDraw.Draw(left);ld.fontmode='1'
                    ld.text((12,12),'1943 - engine 1943',font=FONT,fill='white');ld.text((22,260),'Este valor de arma nao e reconhecido',font=FONT,fill='white');ld.text((22,286),'pelo engine 1943.',font=FONT,fill='white')
                out.paste(left,(0,26));out.paste(panel('1943h11000',weapon,frame,n),(464,26));d.text((10,616),phase(n),font=SMALL,fill='white');frames.append(out)
            info=save_gif(root/'comparacao'/f'{weapon:02X}_{WEAPONS[weapon]}.gif',frames,period);validation.append(info);print('Comparacao',f'{weapon:02X}',flush=True)
    (root/('validacao_piloto.json' if pilot else 'validacao.json')).write_text(json.dumps(validation,indent=2),encoding='utf-8')

if __name__=='__main__':main()
