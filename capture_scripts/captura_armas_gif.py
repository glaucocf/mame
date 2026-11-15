from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
import os,subprocess,json,sys
base=Path(__file__).resolve().parents[1]
root=base/'captures'/'gifs_armas_01'
if '--colisoes' in sys.argv:root=root/'colisoes'
WEAPONS={0:'normal',1:'auto',2:'shot_gun',3:'shot_gun_plus',4:'three_way',8:'shell',0x10:'laser',0x30:'laser_plus',0x50:'laser_supremo'}
ROMS={'1943h10111':list(WEAPONS)[:7],'1943h11000':list(WEAPONS)}
def capture(job):
    rom,weapon=job;dest=root/'registros'/rom/f'{weapon:02X}_{WEAPONS[weapon]}'
    if dest.exists():
        status=dest/'status.txt'
        if status.exists() and 'resultado=ok' in status.read_text():return f'{rom} {weapon:02X}: existente validado'
        archive=dest.parent/'pilotos_incompletos'/dest.name
        assert root.resolve() in dest.resolve().parents and root.resolve() in archive.resolve().parents
        assert not archive.exists(),archive
        archive.parent.mkdir(exist_ok=True);dest.rename(archive)
    dest.mkdir(parents=True,exist_ok=False)
    state=base/'captures'/rom/'catalogacao_01'/'checkpoint_f0001800.sta'
    meta={'rom':rom,'arma_hex':f'{weapon:02X}','nome':WEAPONS[weapon],'save':str(state),'quadros':420,'protocolo':'1-30 solto;31-150 segurando;151-180 solto;181-300 pulsos de 3 quadros ligado/3 desligado;301-420 solto','rapid_fire':False,'somente_cheat':rom=='1943h11000' and weapon in (1,2),'sprites_exibidos':'registros 10-2D; jogador e pools de tiros; coordenadas reais de DMA','cadencia_dma':1,'cadencia_gif':2}
    (dest/'metadados.json').write_text(json.dumps(meta,indent=2),encoding='utf-8')
    args=[str(base/'1943h.exe'),rom,'-noreadconfig','-rompath','roms','-state',str(state),'-nothrottle','-frameskip','0','-noautoframeskip','-video','none','-sound','none','-noplugins','-nocheat','-skip_gameinfo','-cfg_directory',str(dest/'cfg'),'-autoboot_delay','0','-autoboot_script','capture_scripts/captura_armas_gif.lua']
    with (dest/'mame.log').open('w') as log:
        subprocess.run(args,cwd=base,env=dict(os.environ,DEST=dest.as_posix(),WEAPON=str(weapon)),stdout=log,stderr=subprocess.STDOUT,check=True,timeout=90,creationflags=subprocess.CREATE_NO_WINDOW)
    assert 'resultado=ok' in (dest/'status.txt').read_text(),dest
    return f'{rom} {weapon:02X}: 420 quadros capturados'
if __name__=='__main__':
    jobs=[('1943h10111',0)] if '--piloto' in sys.argv else [(rom,weapon) for rom,values in ROMS.items() for weapon in values]
    if '--colisoes' in sys.argv:jobs=[(r,w) for r,w in jobs if (r=='1943h10111' and w in (8,16)) or (r=='1943h11000' and w in (2,3,8,16,48,80))]
    with ThreadPoolExecutor(max_workers=2) as pool:
        for result in pool.map(capture,jobs):print(result,flush=True)
