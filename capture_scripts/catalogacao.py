from pathlib import Path
import json
import os
import subprocess
import sys

base=Path(__file__).resolve().parents[1]
rom=sys.argv[1]
run=sys.argv[2] if len(sys.argv)>2 else 'catalogacao_01'
frames=sys.argv[3] if len(sys.argv)>3 else '450000'
dest=base/'captures'/rom/run
dest.mkdir(parents=True,exist_ok=False)
metadata={'rom':rom,'cadencia_imagens':4,'cadencia_memoria':1,'limite_quadros':int(frames),'frameskip':0,'tiro':'somente na fase 16 apos observacao','registros':'nascimentos candidatos por transicao do campo +08; confirmar semantica por familia','dma':'4107 bytes por registro: quadro uint32, sequencia uint32, banco uint8, camadas uint8, controle uint8, RAM F000-FFFF'}
(dest/'metadados.json').write_text(json.dumps(metadata,indent=2),encoding='utf-8')
args=[str(base/'1943h.exe'),rom,'-noreadconfig','-rompath','roms','-nothrottle','-frameskip','0','-noautoframeskip','-video','none','-sound','none','-noplugins','-nocheat','-skip_gameinfo','-cfg_directory',str(dest/'cfg'),'-nvram_directory',str(dest/'nvram'),'-autoboot_delay','0','-autoboot_script','capture_scripts/catalogacao.lua']
with (dest/'mame.log').open('w') as log:
    subprocess.run(args,cwd=base,env=dict(os.environ,DEST=dest.as_posix(),FRAMES=frames),stdout=log,stderr=subprocess.STDOUT,check=True,timeout=3600)
print((dest/'status.txt').read_text(),flush=True)
