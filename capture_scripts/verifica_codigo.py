from pathlib import Path
import os
import subprocess

base=Path(__file__).resolve().parents[1]
state=base/'captures/1943h10111/campanha/campanha_com_tiro_01/fase_02_f0020292.sta'
for mode in ('controle','combinacao','somente_p1'):
    dest=base/'captures/1943h10111/analise_codigo_fase03'/mode
    dest.mkdir(parents=True,exist_ok=True)
    args=[str(base/'1943h.exe'),'1943h10111','-noreadconfig','-rompath','roms','-state',str(state),'-nothrottle','-frameskip','0','-video','none','-sound','none','-skip_gameinfo','-cfg_directory',str(dest/'cfg'),'-autoboot_delay','0','-autoboot_script','capture_scripts/verifica_codigo.lua']
    with (dest/'mame.log').open('w') as log:
        subprocess.run(args,cwd=base,env=dict(os.environ,DEST=dest.as_posix(),CODIGO='0' if mode=='controle' else '1',P2='1' if mode=='combinacao' else '0'),stdout=log,stderr=subprocess.STDOUT,timeout=60,check=True)
    rows=(dest/'arma.csv').read_text().splitlines()[1:]
    print(mode,sorted({line.split(',')[1] for line in rows}))
