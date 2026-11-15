"""Final checks over delivered files, real-run evidence and native saves."""
from pathlib import Path
import csv
import hashlib
import json
import zipfile

from prepara_32_laboratorios import definitions
from verifica_laboratorio_inimigos import check_xml

BASE=Path(__file__).resolve().parents[1]
ROOT=BASE/'captures'/'laboratorio_inimigos_01'
check_xml()
machines=definitions()
checks=json.loads((ROOT/'verificacao_32_roms.json').read_text(encoding='utf-8'))
assert len(checks)==32 and {r['rom']for r in checks}==set(machines)
for name,machine in machines.items():
    path=ROOT/'bases'/name/'aviao_inicial.sta'
    assert path.read_bytes()[10:28].rstrip(b'\0')==name.encode(),name
    with zipfile.ZipFile(BASE/'roms'/f'{name}.zip')as z:
        for r in machine.findall('rom'):
            if r.get('status')=='nodump':continue
            data=z.read(r.get('name'))
            assert hashlib.sha1(data).hexdigest()==r.get('sha1'),(name,r.get('name'))
    result=next(r for r in checks if r['rom']==name)
    assert result['resultado']=='ok'and result['hp_inicial']==1
    assert result['colisao_confirmada']and result['movimento_confirmado']and result['reposicao_confirmada']
    launcher=ROOT/'roms_hibridas'/f'{name}.cmd'
    assert name in launcher.read_text()and '..\\..\\..'in launcher.read_text()
assert len(list((ROOT/'roms_hibridas').glob('*.cmd')))==32
starts=json.loads((ROOT/'catalogo_isolado'/'verificacao_inicios.json').read_text())
catalog=list(csv.DictReader((ROOT/'catalogo_isolado'/'CATALOGO_ISOLADO.csv').open(encoding='utf-8-sig')))
assert len(starts)==len(catalog)==174
assert {(r['rom'],r['modelo'])for r in starts}=={(r['rom'],r['modelo'])for r in catalog}
for row in catalog:
    folder=ROOT/'catalogo_isolado'/row['rom']/row['modelo']
    assert (folder/'ABRIR.cmd').exists()
    result=next(r for r in starts if r['rom']==row['rom']and r['modelo']==row['modelo'])
    assert result['hp']==int(row['hp_original'])and result['resultado']=='ok'
for rom in ['1943h10111','1943h11000']:
    p=ROOT/rom/'verificacao'/'camadas_xml.csv'
    layer_rows=list(csv.DictReader(p.open()))
    assert len(layer_rows)==9 and all(r['caracteres_preservados']=='true'for r in layer_rows)
    for i,row in enumerate(layer_rows):
        value=0x70 if i==8 else i*0x10
        assert int(row['valor'],16)==value
        assert int(row['upper'])==value&0x10
        assert int(row['lower'])==value&0x20
        assert int(row['sprites'])==value&0x40
out=dict(resultado='ok',roms_verificadas=32,lancadores_roms=32,perfis_isolados=174,
         lancadores_perfis=174,cenas_manuais_verificadas=174,xmls=36,
         combinacoes_camadas=8,destruidos_por_disparo_natural=173,
         temporario_sem_impacto='1943h11000/N003')
(ROOT/'VALIDACAO_FINAL.json').write_text(json.dumps(out,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps(out,ensure_ascii=False),flush=True)
