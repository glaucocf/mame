from pathlib import Path
import os
import subprocess
import csv
import sys
from collections import Counter

base=Path(__file__).resolve().parents[1]
fire='--fire' in sys.argv
dest=base/'captures/1943h10111/primeiros_objetos'/('rastreamento_com_tiro' if fire else 'rastreamento')
dest.mkdir(parents=True,exist_ok=True)
args=[str(base/'1943h.exe'),'1943h10111','-noreadconfig','-rompath','roms','-nothrottle','-frameskip','0','-video','none','-sound','none','-skip_gameinfo','-cfg_directory',str(dest/'cfg'),'-autoboot_delay','0','-autoboot_script','capture_scripts/rastreia_primeiros_objetos.lua']
with (dest/'mame.log').open('w') as log:
    subprocess.run(args,cwd=base,env=dict(os.environ,DEST=dest.as_posix(),FIRE='1' if fire else '0'),stdout=log,stderr=subprocess.STDOUT,check=True,timeout=60)
rows=list(csv.DictReader((dest/'escritas.csv').read_text().splitlines()))
print('escritas',len(rows))
for slot in ('2E','2F','30','3E','42'):
    selected=[r for r in rows if r['registro']==slot]
    print('registro',slot,'primeiras',selected[:12])
    print('PCs',Counter((r['pc'],r['campo']) for r in selected).most_common(12))
