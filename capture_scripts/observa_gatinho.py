from pathlib import Path
import zipfile,os,subprocess,json
base=Path(__file__).resolve().parents[1]
with zipfile.ZipFile(base/'roms/1943h10111.zip') as archive:prefix=archive.read('01.12d')[0x7270:0x7270+28]
for rom in ['1943h10111','1943h11000']:
    with zipfile.ZipFile(base/'roms'/f'{rom}.zip') as archive:fixed=archive.read('01.12d')
    matches=[i for i in range(len(fixed)-32) if fixed[i:i+10]==prefix[:10] and fixed[i+11:i+28]==prefix[11:]]
    assert len(matches)==1,(rom,matches)
    template=matches[0]
    dest=base/'captures'/rom/'gatinho_teste_01'
    if dest.exists():print(rom,'teste existente preservado');continue
    dest.mkdir(exist_ok=False)
    state=base/'captures'/rom/'catalogacao_01'/'checkpoint_f0001800.sta'
    (dest/'metadados.json').write_text(json.dumps({'rom':rom,'template_ROM':f'{template:04X}','state':str(state),'teste':'copia do template nativo para registro livre; aproximacao do jogador no quadro 80; nenhuma escrita na arma'},indent=2),encoding='utf-8')
    args=[str(base/'1943h.exe'),rom,'-noreadconfig','-rompath','roms','-state',str(state),'-nothrottle','-frameskip','0','-video','none','-sound','none','-noplugins','-nocheat','-skip_gameinfo','-cfg_directory',str(dest/'cfg'),'-autoboot_delay','0','-autoboot_script','capture_scripts/observa_gatinho.lua']
    with (dest/'mame.log').open('w') as log:
        subprocess.run(args,cwd=base,env=dict(os.environ,DEST=dest.as_posix(),TEMPLATE_ADDR=str(template)),stdout=log,stderr=subprocess.STDOUT,timeout=45,check=True)
    print(rom,f'template {template:04X}',(dest/'eventos.csv').read_text(),flush=True)
