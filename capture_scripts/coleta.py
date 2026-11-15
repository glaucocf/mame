from pathlib import Path
import os, sys, subprocess
base = Path(__file__).resolve().parents[1]
rom, mode = sys.argv[1:3]
dest = base / 'captures' / rom / mode
dest.mkdir(parents=True, exist_ok=True)
if mode in ('object_test','vram_character_code'):
    for palette in range(16 if mode=='object_test' else 32):
        (dest / f'pal_{palette:02X}').mkdir(exist_ok=True)
args = [str(base/'1943h.exe'), rom, '-noreadconfig','-rompath','roms','-state_directory','sta','-state','q','-nothrottle','-noautoframeskip','-frameskip','0','-video','none','-sound','none','-window','-skip_gameinfo','-snapshot_directory',str(dest),'-cfg_directory',str(dest/'cfg'),'-autoboot_delay','0','-autoboot_script','capture_scripts/coleta.lua']
with (dest/'mame.log').open('w') as log:
    subprocess.run(args,cwd=base,env=dict(os.environ,DEST=str(dest).replace('\\','/'),MODE=mode),stdout=log,stderr=subprocess.STDOUT,timeout=600,check=True)
