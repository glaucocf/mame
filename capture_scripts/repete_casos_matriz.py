from pathlib import Path
import csv,json,re,subprocess,os
base=Path(__file__).resolve().parents[1];root=base/'captures'/'matriz_colisoes_01'
issues=json.loads((root/'REVISAR_ARITMETICA.json').read_text(encoding='utf-8'))
def read(path):
    with path.open(newline='')as stream:return list(csv.DictReader(stream))
def write(path,rows,fields=None):
    if not fields:fields=list(rows[0])
    with path.open('w',newline='',encoding='utf-8')as stream:
        w=csv.DictWriter(stream,fieldnames=fields);w.writeheader();w.writerows(rows)
for rom in ['1943h10111','1943h11000']:
    selected=[r for r in issues if r['rom']==rom]
    if not selected:continue
    dest=root/(rom+'_repeticoes');dest.mkdir(exist_ok=True)
    (dest/'casos_anteriores.json').write_text(json.dumps(selected,indent=2),encoding='utf-8')
    jobs=[];datasets={}
    for row in selected:
        folder=Path(row['fonte']).parent;assert root.resolve()in folder.resolve().parents
        matches={m.group(1):m.group(0)for m in re.finditer(r'\{id="([^"]+)"[^{}]*\}',(folder/'jobs.lua').read_text(encoding='utf-8'))}
        jobs.append(matches[row['caso']]);datasets.setdefault(folder,set()).add(row['caso'])
    (dest/'jobs.lua').write_text('return {'+','.join(jobs)+'}',encoding='utf-8')
    args=[str(base/'1943h.exe'),rom,'-noreadconfig','-rompath','roms','-nothrottle','-frameskip','0','-noautoframeskip','-video','none','-sound','none','-noplugins','-nocheat','-skip_gameinfo','-cfg_directory',str(dest/'cfg'),'-autoboot_delay','0','-autoboot_script','capture_scripts/executa_matriz_colisoes.lua']
    with(dest/'mame.log').open('w')as log:
        subprocess.run(args,cwd=base,env=dict(os.environ,DEST=dest.as_posix(),JOBS=(dest/'jobs.lua').as_posix(),ROM=rom,DESTRUCTION='0',KNOWN=''),stdout=log,stderr=subprocess.STDOUT,timeout=180,check=True,creationflags=subprocess.CREATE_NO_WINDOW)
    result=read(dest/'resultados.csv');assert len(result)==len(selected)
    bycase={r['caso']:r for r in result};events=read(dest/'eventos.csv')
    for folder,cases in datasets.items():
        old=read(folder/'resultados.csv');fields=list(old[0]);updated=[bycase[r['caso']]if r['caso']in cases else r for r in old]
        oldevents=read(folder/'eventos.csv')
        write(dest/(folder.name+'_eventos_anteriores.csv'),[r for r in oldevents if r['caso']in cases])
        merged=[r for r in oldevents if r['caso']not in cases]+[r for r in events if r['caso']in cases]
        order={r['caso']:i for i,r in enumerate(old)};merged.sort(key=lambda r:(order[r['caso']],int(r['quadro'])))
        write(folder/'resultados.csv',updated,fields);write(folder/'eventos.csv',merged)
    print(rom,len(result),'casos repetidos e substituidos; evidencias anteriores preservadas',flush=True)
