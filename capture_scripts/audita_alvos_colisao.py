from pathlib import Path
from collections import Counter
import csv,zipfile,json
base=Path(__file__).resolve().parents[1]
for rom in ['1943h10111','1943h11000']:
    with zipfile.ZipFile(base/'roms'/f'{rom}.zip') as archive:
        fixed=archive.read('01.12d');banks=archive.read('02.13d')+archive.read('03.14d')
    rows=list(csv.DictReader((base/'captures'/rom/'catalogacao_01'/'analise'/'modelos.csv').open(encoding='utf-8-sig')))
    audit=[]
    for row in rows:
        template=int(row['modelo_ROM'],16);bank=int(row['banco']);slot=int(row['registro_exemplo'],16)
        data=fixed[template:template+32] if template<0x8000 else banks[bank*0x4000+template-0x8000:bank*0x4000+template-0x8000+32]
        audit.append({'modelo':row['modelo'],'banco':bank,'template':row['modelo_ROM'],'quadro':int(row['primeiro_quadro']),'slot':row['registro_exemplo'],'estado_08':data[8],'flags_09':data[9],'tipo_0A':data[10],'resistencia_0B':data[11],'caixa_0C':data[12],'caixa_0D':data[13],'referencia':row['referencia_1C'],'rotulo':row['rotulo']})
    print(rom,'total',len(audit),'flags',dict(Counter((r['flags_09'],r['tipo_0A']&15) for r in audit)),flush=True)
    for row in audit:print(json.dumps(row,ensure_ascii=False),flush=True)
    folder=base/'captures'/'matriz_colisoes_01';folder.mkdir(exist_ok=True)
    (folder/f'auditoria_{rom}.json').write_text(json.dumps(audit,ensure_ascii=False,indent=2),encoding='utf-8')
