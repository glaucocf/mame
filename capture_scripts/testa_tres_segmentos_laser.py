from pathlib import Path
import csv,json,subprocess,os
base=Path(__file__).resolve().parents[1];root=base/'captures'/'matriz_colisoes_01';rom='1943h10111'
dest=root/(rom+'_laser_tres_segmentos');dest.mkdir(exist_ok=True)
def quote(v):return json.dumps(str(v).replace('\\','/'),ensure_ascii=False)
with(root/rom/'preparacao.csv').open()as stream:records={r['modelo']:r for r in csv.DictReader(stream)}
audit={r['modelo']:r for r in json.loads((root/f'auditoria_{rom}.json').read_text(encoding='utf-8'))}
jobs=[]
for model in ['M005','M011','M018','M051']:
    row=records[model]
    for i,slot in enumerate([0xf380,0xf3a0,0xf3c0],1):
        case=f'{model}_laser_segmento_{i}'
        jobs.append('{id='+quote(case)+',model='+quote(model)+',mode="arma",weapon=16,segment_base='+str(slot)+',checkpoint='+quote(root/rom/(model+'.sta'))+',target='+str(int(row['endereco'],16))+',reference='+str(int(audit[model]['referencia'],16))+',output='+quote(dest/case)+'}')
(dest/'jobs.lua').write_text('return {'+','.join(jobs)+'}',encoding='utf-8')
args=[str(base/'1943h.exe'),rom,'-noreadconfig','-rompath','roms','-nothrottle','-frameskip','0','-noautoframeskip','-video','none','-sound','none','-noplugins','-nocheat','-skip_gameinfo','-cfg_directory',str(dest/'cfg'),'-autoboot_delay','0','-autoboot_script','capture_scripts/executa_matriz_colisoes.lua']
with(dest/'mame.log').open('w')as log:
    subprocess.run(args,cwd=base,env=dict(os.environ,DEST=dest.as_posix(),JOBS=(dest/'jobs.lua').as_posix(),ROM=rom,DESTRUCTION='0',KNOWN=''),stdout=log,stderr=subprocess.STDOUT,timeout=90,check=True,creationflags=subprocess.CREATE_NO_WINDOW)
with(dest/'resultados.csv').open()as stream:rows=list(csv.DictReader(stream))
assert len(rows)==12 and 'estado=concluido'in(dest/'status.txt').read_text()
for row in rows:
    part=int(row['caso'].rsplit('_',1)[1]);hp=int(row['resistencia_inicial']);after=int(row['resistencia_final']);force=int(row['forca_inicial']);remaining=int(row['forca_final'])
    assert int(row['tiro'],16)==[0xf380,0xf3a0,0xf3c0][part-1],row
    assert force==48,row
    if hp<force:assert row['resultado']=='atingiu_e_continuou'and after==0 and remaining==force-hp,row
    else:assert row['resultado']=='atingiu_e_consumiu_tiro'and after==hp-force,row
with(dest/'eventos.csv').open()as stream:events=list(csv.DictReader(stream))
assert len([r for r in events if r['tipo']=='grafico_tiro'])==12
assert all(int(r['antes'])==0x96 for r in events if r['tipo']=='grafico_tiro')
print('12 impactos isolados conferidos; tres segmentos com forca 48 e grafico 096.',flush=True)
for row in rows:print(row['caso'],'alvo',row['resistencia_inicial'],'->',row['resistencia_final'],'tiro',row['forca_inicial'],'->',row['forca_final'],row['resultado'],flush=True)
