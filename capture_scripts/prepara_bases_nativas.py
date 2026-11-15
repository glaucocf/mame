from pathlib import Path
import os
import subprocess
import sys
import zipfile
import re

BASE = Path(__file__).resolve().parents[1]
rom = sys.argv[1]
assert re.fullmatch(r'1943h[01]{5}', rom)
dest = BASE/'captures'/'laboratorio_inimigos_01'/'bases_nativas'/rom
dest.mkdir(parents=True, exist_ok=True)
template = 0x88F4 if rom[6] == '0' else 0x88F9
with zipfile.ZipFile(BASE/'roms'/f'{rom}.zip') as z:
    bank = z.read('02.13d')
    reference = int.from_bytes(bank[template-0x8000+28:template-0x8000+30], 'little')
args = [str(BASE/'1943h.exe'), rom, '-noreadconfig', '-rompath', 'roms', '-nothrottle',
        '-frameskip', '0', '-noautoframeskip', '-video', 'none', '-sound', 'none',
        '-noplugins', '-nocheat', '-skip_gameinfo', '-cfg_directory', str(dest/'cfg'),
        '-autoboot_delay', '0', '-autoboot_script', 'capture_scripts/salva_aviao_nativo.lua']
with (dest/'mame.log').open('w') as log:
    subprocess.run(args, cwd=BASE, env=dict(os.environ, DEST=dest.as_posix(),
         TEMPLATE=str(template), REFERENCE=str(reference)), stdout=log, stderr=subprocess.STDOUT,
         check=True, timeout=120, creationflags=subprocess.CREATE_NO_WINDOW)
assert (dest/'aviao_inicial.sta').exists(), dest
assert (dest/'alvo.json').exists(), dest
print(f'{rom}: avião nativo salvo; referência {reference:04X}', flush=True)
