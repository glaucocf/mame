"""Run every proven hittable profile alone, using its original checkpoint."""
from pathlib import Path
import csv
import json
import os
import subprocess
import sys

BASE = Path(__file__).resolve().parents[1]
MATRIX = BASE/'captures'/'matriz_colisoes_01'
ROOT = BASE/'captures'/'laboratorio_inimigos_01'/'catalogo_isolado'


def prepare(rom, pilot=False):
    catalog = list(csv.DictReader((MATRIX/'CATALOGO_FUNCIONAL.csv').open(encoding='utf-8-sig')))
    results = list(csv.DictReader((MATRIX/'MATRIZ_ARMAS.csv').open(encoding='utf-8-sig')))
    eligible = [r for r in catalog if r['rom']==rom and r['funcao_por_execucao'] in
                ('objeto atingivel','alvo de multiplas pecas','alvo composto grande')]
    assert len(eligible)==87
    if pilot:
        ids = ['M005','M009','M011','M016','M018','M051','N003'] if rom=='1943h10111' else ['M006','M010','M012','M017','M019','M109','N003']
        eligible = [r for r in eligible if r['modelo'] in ids]
    dest=ROOT/(rom+('_piloto' if pilot else ''))
    dest.mkdir(parents=True,exist_ok=True)
    jobs=[]
    for row in eligible:
        prior = next(r for r in results if r['rom']==rom and r['modelo']==row['modelo'] and r['rotina'] in ('alvo','alvo_multisprite','alvo_grande'))
        source=Path(row['save']) if row['save'] else MATRIX/rom/(row['modelo']+'.sta')
        assert source.exists(),source
        folder=dest/row['modelo'];folder.mkdir(exist_ok=True)
        jobs.append(dict(id=row['modelo'],checkpoint=source.as_posix(),target=int(prior['alvo'],16),
                         reference=int(row['referencia'],16),hp=int(prior['resistencia_inicial']),
                         routine=prior['rotina'],label=row['rotulo_visual'],output=folder.as_posix()))
    def lua(v):return str(v) if isinstance(v,int) else json.dumps(v,ensure_ascii=False)
    (dest/'jobs.lua').write_text('return {\n'+',\n'.join('{'+','.join(k+'='+lua(v) for k,v in j.items())+'}' for j in jobs)+'\n}\n',encoding='utf-8')
    (dest/'jobs.json').write_text(json.dumps(jobs,ensure_ascii=False,indent=2),encoding='utf-8')
    return dest


if __name__=='__main__':
    rom=sys.argv[1];pilot='--piloto'in sys.argv
    dest=prepare(rom,pilot)
    args=[str(BASE/'1943h.exe'),rom,'-noreadconfig','-rompath','roms','-frameskip','0',
          '-noautoframeskip','-nothrottle','-video','none','-sound','none','-noplugins',
          '-nocheat','-skip_gameinfo','-cfg_directory',str(dest/'cfg'),'-autoboot_delay','0',
          '-autoboot_script','capture_scripts/isola_catalogo.lua']
    with (dest/'mame.log').open('w')as log:
        subprocess.run(args,cwd=BASE,env=dict(os.environ,DEST=dest.as_posix(),
              JOBS=(dest/'jobs.lua').as_posix(),ROM=rom),stdout=log,stderr=subprocess.STDOUT,
              timeout=1800,check=True,creationflags=subprocess.CREATE_NO_WINDOW)
    assert 'concluido' in (dest/'status.txt').read_text(),dest
    print(f'{rom}: isolamento finalizado, {dest}',flush=True)
