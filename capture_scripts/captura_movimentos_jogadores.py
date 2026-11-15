from pathlib import Path
import os
import subprocess
import sys

BASE=Path(__file__).resolve().parents[1]
rom=sys.argv[1]
assert rom in ['1943h10000','1943h11111']
dest=BASE/'captures'/'movimentos_jogadores_01'/rom
if '--cold' in sys.argv:dest=dest/'cold'
dest.mkdir(parents=True,exist_ok=True)
state=BASE/'captures'/'laboratorio_inimigos_01'/'bases'/rom/'aviao_inicial.sta'
args=[str(BASE/'1943h.exe'),rom,'-noreadconfig','-rompath','roms','-nothrottle','-frameskip','0','-noautoframeskip',
      '-video','none','-sound','none','-noplugins','-nocheat','-skip_gameinfo','-cfg_directory',str(dest/'cfg'),
      '-autoboot_delay','0','-autoboot_script','capture_scripts/captura_movimentos_jogadores.lua']
with(dest/'mame.log').open('w')as log:
    subprocess.run(args,cwd=BASE,env=dict(os.environ,DEST=dest.as_posix(),CHECKPOINT=state.as_posix(),COLD='1'if '--cold'in sys.argv else'0'),stdout=log,stderr=subprocess.STDOUT,
                   check=True,timeout=120,creationflags=subprocess.CREATE_NO_WINDOW)
print(rom,(dest/'status.txt').read_text(),flush=True)
assert 'resultado=ok'in(dest/'status.txt').read_text()
