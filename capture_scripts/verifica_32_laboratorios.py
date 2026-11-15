from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
import json
import os
import subprocess

from laboratorio_inimigo import BASE, ROOT, prepare, command
from verifica_laboratorio_inimigos import check_run


def run(rom):
    dest, config = prepare(rom, True)
    with (dest/'mame.log').open('w') as log:
        subprocess.run(command(rom,dest,True),cwd=BASE,
             env=dict(os.environ,LAB_CONFIG=str(config)),stdout=log,stderr=subprocess.STDOUT,
             timeout=90,check=True,creationflags=subprocess.CREATE_NO_WINDOW)
    check_run(dest)
    data=json.loads((dest/'validacao.json').read_text())
    data['lancador']=str(ROOT/'roms_hibridas'/f'{rom}.cmd')
    assert Path(data['lancador']).exists()
    return data


if __name__=='__main__':
    roms=[f'1943h{i:05b}'for i in range(32)]
    with ThreadPoolExecutor(max_workers=2)as pool:
        results=list(pool.map(run,roms))
    assert len(results)==32
    (ROOT/'verificacao_32_roms.json').write_text(json.dumps(results,ensure_ascii=False,indent=2),encoding='utf-8')
    print('OK: todas as 32 ROMs carregaram, isolaram o alvo e confirmaram movimento, reposicao e impacto natural.',flush=True)
