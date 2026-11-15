from pathlib import Path
import csv,json,subprocess,os,sys
from captura_armas_gif import ROMS
base=Path(__file__).resolve().parents[1];root=base/'captures'/'matriz_colisoes_01'
rom=sys.argv[1];destruction='--destruicao' in sys.argv;late='--longos'in sys.argv
def quote(value):return json.dumps(str(value).replace('\\','/'),ensure_ascii=False)
with (root/(rom+('_destruicao_longa'if late else'_destruicao'))/'novos_estados.csv').open()as stream:new=list(csv.DictReader(stream))
all_new=[dict(row,modelo=f'{"T"if late else"N"}{i:03d}') for i,row in enumerate(new,1)]
selected=[row for row in all_new if int(row['tipo'],16)&15==0]
dest=root/(rom+('_destruicao_tardios'if destruction and late else'_destruicao_novos' if destruction else '_ensaios_tardios'if late else'_ensaios_novos'));dest.mkdir(exist_ok=True);(dest/'novos').mkdir(exist_ok=True)
if destruction:
    with (root/(rom+'_ensaios_novos')/'resultados.csv').open()as stream:proven=list(csv.DictReader(stream))
    eligible={r['modelo'] for r in proven if r['rotina']in('alvo','alvo_multisprite','alvo_grande')}
    selected=[row for row in selected if row['modelo']in eligible]
jobs=[]
for row in selected:
    path=Path(row['arquivo']);assert path.exists()and root.resolve()in path.resolve().parents
    weapons=([16]if rom=='1943h10111'else[80])if destruction else ROMS[rom]+[-1]
    for weapon in weapons:
        mode='contato'if weapon==-1 else'arma';case=row['modelo']+('_contato'if weapon==-1 else f'_arma_{weapon:02X}')
        jobs.append('{id='+quote(case)+',model='+quote(row['modelo'])+',mode='+quote(mode)+',weapon='+str(max(weapon,0))+',checkpoint='+quote(path)+',target='+str(int(row['endereco'],16))+',reference='+str(int(row['referencia'],16))+',output='+quote(dest/case)+'}')
(dest/'jobs.lua').write_text('return {\n'+',\n'.join(jobs)+'\n}',encoding='utf-8')
(dest/'catalogo_novos.json').write_text(json.dumps(all_new,indent=2,ensure_ascii=False),encoding='utf-8')
audit=json.loads((root/f'auditoria_{rom}.json').read_text(encoding='utf-8'))
known=[f"L_{r['banco']}_{r['template']}_{r['referencia']}"for r in audit]+[r['chave']for r in new]
(dest/'conhecidos.lua').write_text('return {'+','.join('['+quote(key)+']=true'for key in known)+'}',encoding='utf-8')
args=[str(base/'1943h.exe'),rom,'-noreadconfig','-rompath','roms','-nothrottle','-frameskip','0','-noautoframeskip','-video','none','-sound','none','-noplugins','-nocheat','-skip_gameinfo','-cfg_directory',str(dest/'cfg'),'-autoboot_delay','0','-autoboot_script','capture_scripts/executa_matriz_colisoes.lua']
with(dest/'mame.log').open('w')as log:
    subprocess.run(args,cwd=base,env=dict(os.environ,DEST=dest.as_posix(),JOBS=(dest/'jobs.lua').as_posix(),KNOWN=(dest/'conhecidos.lua').as_posix(),ROM=rom,DESTRUCTION='1'if destruction else'0'),stdout=log,stderr=subprocess.STDOUT,timeout=900,check=True,creationflags=subprocess.CREATE_NO_WINDOW)
print(rom,len(jobs),'ensaios de novos objetos finalizados',flush=True)
