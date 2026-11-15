from pathlib import Path
import csv,json,subprocess,os,sys
base=Path(__file__).resolve().parents[1];root=base/'captures'/'matriz_colisoes_01';rom='1943h11000'
pilot='--piloto'in sys.argv
late='--tardios'in sys.argv
dest=root/(rom+('_ensaios_laser_secundario_tardio'if late else'_ensaios_laser_secundario_piloto'if pilot else'_ensaios_laser_secundario'));dest.mkdir(exist_ok=True)
def quote(v):return json.dumps(str(v).replace('\\','/'),ensure_ascii=False)
audit={r['modelo']:r for r in json.loads((root/f'auditoria_{rom}.json').read_text(encoding='utf-8'))}
with(root/rom/'preparacao.csv').open()as stream:old=list(csv.DictReader(stream))
records=[]
for row in old:
    path=root/rom/(row['modelo']+'.sta')
    if path.exists():records.append((row['modelo'],path,int(row['endereco'],16),int(audit[row['modelo']]['referencia'],16)))
with(root/(rom+'_destruicao')/'novos_estados.csv').open()as stream:new=list(csv.DictReader(stream))
for i,row in enumerate(new,1):
    if int(row['tipo'],16)&15==0:records.append((f'N{i:03d}',Path(row['arquivo']),int(row['endereco'],16),int(row['referencia'],16)))
if late:
    records=[]
    with(root/(rom+'_destruicao_longa')/'novos_estados.csv').open()as stream:late_rows=list(csv.DictReader(stream))
    for i,row in enumerate(late_rows,1):
        if int(row['tipo'],16)&15==0:records.append((f'T{i:03d}',Path(row['arquivo']),int(row['endereco'],16),int(row['referencia'],16)))
jobs=[]
if pilot:records=[r for r in records if r[0]in('M006','M019','M109')]
for model,path,target,reference in records:
    for weapon in [16,48,80]:
        case=f'{model}_arma_{weapon:02X}_sec09F'
        jobs.append('{id='+quote(case)+',model='+quote(model)+',mode="arma",weapon='+str(weapon)+',secondary=true,checkpoint='+quote(path)+',target='+str(target)+',reference='+str(reference)+',output='+quote(dest/case)+'}')
(dest/'jobs.lua').write_text('return {'+','.join(jobs)+'}',encoding='utf-8')
args=[str(base/'1943h.exe'),rom,'-noreadconfig','-rompath','roms','-nothrottle','-frameskip','0','-noautoframeskip','-video','none','-sound','none','-noplugins','-nocheat','-skip_gameinfo','-cfg_directory',str(dest/'cfg'),'-autoboot_delay','0','-autoboot_script','capture_scripts/executa_matriz_colisoes.lua']
with(dest/'mame.log').open('w')as log:
    subprocess.run(args,cwd=base,env=dict(os.environ,DEST=dest.as_posix(),JOBS=(dest/'jobs.lua').as_posix(),ROM=rom,DESTRUCTION='0',KNOWN=''),stdout=log,stderr=subprocess.STDOUT,timeout=900,check=True,creationflags=subprocess.CREATE_NO_WINDOW)
print(len(jobs),'ensaios dos componentes 09F finalizados',flush=True)
