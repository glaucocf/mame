from pathlib import Path
from PIL import Image,ImageSequence
import csv,json,struct,zipfile,zlib,html
from captura_armas_gif import WEAPONS,ROMS
from monta_gifs_armas import NAMES

base=Path(__file__).resolve().parents[1];root=base/'captures'/'gifs_armas_01'
validation=json.loads((root/'validacao.json').read_text())
assert len(validation)==25
summary=[]
for rom,weapons in ROMS.items():
    for weapon in weapons:
        folder=root/'registros'/rom/f'{weapon:02X}_{WEAPONS[weapon]}'
        data=zlib.decompress((folder/'dma.zlib').read_bytes());assert len(data)%4101==0
        maximum=0;peak=0;codes=set()
        for off in range(0,len(data),4101):
            frame=struct.unpack_from('<I',data,off)[0];raw=data[off+5:off+4101];pieces=0
            for slot in range(0x1c,0x2e):
                low,attr,y,x=raw[slot*32:slot*32+4];x-=((attr&16)<<4)
                if -15<=x<256 and 1<=y<240:
                    pieces+=1;codes.add(f'{low+((attr&0xe0)<<3):03X}/p{attr&15:X}')
            if pieces>maximum:maximum=pieces;peak=frame
        assert maximum>0,(rom,weapon,'nenhum projetil capturado')
        rows=list(csv.DictReader((folder/'quadros.csv').open()))
        assert len(rows)==420
        for n,row in enumerate(rows,1):
            fire=(31<=n<=150) or (181<=n<=300 and (n-181)%6<3)
            assert int(row['botao'])==int(fire)
        summary.append({'rom':rom,'arma':f'{weapon:02X}','maximo_pecas_tiros_visiveis':maximum,'quadro_amostra':peak,'graficos_paletas_tiros':sorted(codes)})
for item in validation:
    path=Path(item['arquivo']);assert path.exists() and path.stat().st_size>0
    with Image.open(path) as gif:
        assert gif.n_frames==210 and gif.info['loop']==0
        assert sum(frame.info['duration'] for frame in ImageSequence.Iterator(gif))==7040
    if 'rom' in item:assert all(check['fracao_tela_completa_sprites_igual']==1 for check in item['comparacao_com_MAME'])
(root/'conferencia_final.json').write_text(json.dumps({'gifs':25,'comparativos':9,'individuais':16,'quadros_originais_por_teste':420,'quadros_gif':210,'duracao_ms':7040,'quadros_conferidos_pixel_a_pixel_MAME':80,'projecao_tiros':summary},indent=2),encoding='utf-8')

intro='São nove comparativos, um por valor de arma, e dezesseis GIFs individuais. As ROMs são 1943h10111 (engine 1943, arte Kai) e 1943h11000 (engine Kai, arte 1943).'
protocol='Cada teste usa o mesmo save inicial e dura 420 quadros do emulador (7,04 s). O GIF conserva um quadro a cada dois, com escala 2× sem suavização e paleta exata. Primeiro o botão fica solto; depois é mantido pressionado por 120 quadros; após uma pausa são feitos toques de três quadros ligado e três desligado. Não foi aplicado o cheat de tiro rápido.'
notes='No Kai, 01 e 02 foram ativados por cheat. O valor 03 é Shot Gun + no 1943 e a opção normal de Shot Gun no Kai. O valor 10 é o laser supremo no 1943 e o primeiro laser no Kai; 30 e 50 pertencem somente ao Kai. Os cenários, inimigos e seus tiros foram omitidos da exportação para destacar o jogador. A lógica da partida permaneceu ativa, incluindo colisões; este conjunto demonstra os disparos e não mede seu alcance máximo.'
readme=['# GIFs das armas\n',intro+'\n',protocol+'\n',notes+'\n','| Valor | Arma | Comparação | 1943h10111 | 1943h11000 |\n| --- | --- | --- | --- | --- |']
cards=[]
for weapon,name in WEAPONS.items():
    filename=f'{weapon:02X}_{name}.gif';compar=f'comparacao/{filename}'
    a=f'1943h10111/{filename}' if weapon in ROMS['1943h10111'] else None;b=f'1943h11000/{filename}'
    readme.append(f"| {weapon:02X} | {NAMES[weapon]} | [GIF]({compar}) | "+(f'[GIF]({a})' if a else 'Não reconhecido')+f' | [GIF]({b}) |')
    individual=(f'<a href="{a}">1943h10111 individual</a>' if a else '1943: valor não reconhecido')+f' · <a href="{b}">1943h11000 individual</a>'
    cards.append(f'<section><h2>{weapon:02X} — {html.escape(NAMES[weapon])}</h2><p><a href="{compar}" download>Baixar comparativo</a> · {individual}</p><img src="{compar}" loading="lazy" alt="Disparo {weapon:02X} comparado nos dois engines"></section>')
readme.extend(['\nOs registros e imagens originais para conferência ficam em `registros/`. `validacao.json` e `conferencia_final.json` registram os testes. Os 80 quadros usados na conferência da imagem completa de sprites coincidiram pixel a pixel com o MAME.','\n[Galeria animada](index.html)'])
(root/'LEIA_ME.md').write_text('\n\n'.join(readme[:4])+'\n\n'+'\n'.join(readme[4:]),encoding='utf-8')
page='<!doctype html><html lang="pt-BR"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>1943 / Kai — GIFs das armas</title><style>body{background:#15191f;color:#eef2f7;font:16px/1.6 system-ui,sans-serif;max-width:1000px;margin:36px auto;padding:0 20px}a{color:#9dcfff}h1{font-size:30px}h2{font-size:22px}section{margin:36px 0 64px}img{display:block;width:100%;max-width:912px;height:auto;image-rendering:pixelated;border:1px solid #333b48}p{max-width:940px}</style><h1>1943 / Kai — GIFs das armas</h1><p>'+html.escape(intro)+'</p><p>'+html.escape(protocol)+'</p><p>'+html.escape(notes)+'</p><p><a href="gifs_armas.zip" download>Baixar todos os GIFs</a> · <a href="LEIA_ME.md">Ler descrição</a></p>'+''.join(cards)+'</html>'
(root/'index.html').write_text(page,encoding='utf-8')
files=[root/'LEIA_ME.md',root/'index.html',root/'validacao.json',root/'conferencia_final.json']+[Path(item['arquivo']) for item in validation]
with zipfile.ZipFile(root/'gifs_armas.zip','w',zipfile.ZIP_DEFLATED,compresslevel=6) as archive:
    for file in files:archive.write(file,file.relative_to(root).as_posix())
with zipfile.ZipFile(root/'gifs_armas.zip') as archive:assert len(archive.namelist())==29 and archive.testzip() is None
print('25 GIFs conferidos; 16 testes com projeteis; 80 imagens completas identicas ao MAME; galeria e ZIP prontos.',flush=True)
print(json.dumps(summary,ensure_ascii=False),flush=True)
