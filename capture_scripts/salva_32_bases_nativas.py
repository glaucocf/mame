from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
import subprocess
import sys

BASE=Path(__file__).resolve().parents[1]


def run(rom):
    p=subprocess.run([sys.executable,'capture_scripts/prepara_bases_nativas.py',rom],
                     cwd=BASE,capture_output=True,text=True,timeout=150,
                     creationflags=subprocess.CREATE_NO_WINDOW)
    if p.returncode:raise RuntimeError(p.stdout+p.stderr)
    print(p.stdout.strip(),flush=True)


if __name__=='__main__':
    with ThreadPoolExecutor(max_workers=2)as pool:
        list(pool.map(run,[f'1943h{i:05b}'for i in range(32)]))
