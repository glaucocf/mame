from pathlib import Path
import os
import subprocess
import sys

base = Path(__file__).resolve().parents[1]
rom, run = sys.argv[1:3]
dest = base / 'captures' / rom / 'campanha' / run
dest.mkdir(parents=True, exist_ok=False)
env = dict(os.environ, DEST=dest.as_posix(), FRAMES=sys.argv[3] if len(sys.argv)>3 else '18000', FIRE=sys.argv[4] if len(sys.argv)>4 else '0', RESUME=sys.argv[5] if len(sys.argv)>5 else '')
args = [str(base/'1943h.exe'), rom, '-noreadconfig', '-rompath','roms','-state_directory','sta','-nothrottle','-frameskip','0','-video','none','-sound','none','-skip_gameinfo','-cfg_directory',str(dest/'cfg'),'-nvram_directory',str(dest/'nvram'),'-autoboot_delay','0','-autoboot_script','capture_scripts/campanha.lua']
with (dest/'mame.log').open('w') as log:
    subprocess.run(args,cwd=base,env=env,stdout=log,stderr=subprocess.STDOUT,check=True,timeout=3600)
