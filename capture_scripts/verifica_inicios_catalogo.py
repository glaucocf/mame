from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
import csv
import json
import os
import subprocess

from laboratorio_inimigo import BASE, ROOT, prepare, command


def run(pair):
    rom,job=pair
    dest,config=prepare(rom,True,job['id'],short=True)
    (dest/'validacao.json').unlink(missing_ok=True)
    with (dest/'mame.log').open('w')as log:
        subprocess.run(command(rom,dest,True),cwd=BASE,env=dict(os.environ,LAB_CONFIG=str(config)),
                       stdout=log,stderr=subprocess.STDOUT,check=True,timeout=60,
                       creationflags=subprocess.CREATE_NO_WINDOW)
    result=json.loads((dest/'validacao.json').read_text())
    assert result['resultado']=='ok'and result['quadros']==45,(rom,job['id'],result)
    assert result['hp_inicial']==job['hp'],(rom,job['id'],result)
    rows=list(csv.DictReader((dest/'quadros.csv').open()))
    assert all(r['outros_inimigos']=='0'and r['camadas']=='40'for r in rows)
    assert (dest/'quadro_0030.png').exists()
    return dict(rom=rom,modelo=job['id'],hp=job['hp'],quadros=45,resultado='ok')


if __name__=='__main__':
    jobs=[]
    for rom in ['1943h10111','1943h11000']:
        jobs.extend((rom,j)for j in json.loads((ROOT/'catalogo_isolado'/rom/'jobs.json').read_text(encoding='utf-8')))
    assert len(jobs)==174
    results=[]
    with ThreadPoolExecutor(max_workers=2)as pool:
        for result in pool.map(run,jobs):
            results.append(result)
            if len(results)%20==0:print(f'{len(results)}/174 cenas manuais verificadas',flush=True)
    (ROOT/'catalogo_isolado'/'verificacao_inicios.json').write_text(json.dumps(results,indent=2),encoding='utf-8')
    print('OK: 174 cenas manuais abriram com o HP esperado, alvo isolado e BG desligados.',flush=True)
