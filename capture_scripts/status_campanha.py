from pathlib import Path
import csv

root=Path(__file__).resolve().parents[1]/'captures'
for rom in ('1943h10111','1943h00111','1943h11000'):
    path=root/rom/'campanha'/'campanha_com_tiro_01'
    lines=(path/'eventos.csv').read_text().splitlines()
    rows=list(csv.DictReader(lines))
    stages=[(r['quadro'],r['fase_E450']) for r in rows if r['evento']=='fase']
    print(rom,'fases',stages,'ultimo',lines[-1],flush=True)
    errors=[r for r in rows if r['evento']=='erro']
    if errors: print('ERROS',errors[:2])
