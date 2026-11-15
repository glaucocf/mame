from pathlib import Path
import csv,json,subprocess,os,sys
from captura_armas_gif import ROMS
base=Path(__file__).resolve().parents[1];root=base/'captures'/'matriz_colisoes_01'
def quote(value):return json.dumps(str(value).replace('\\','/'),ensure_ascii=False)
def run(rom,pilot=False):
    long='--observacao-longa' in sys.argv;destruction='--destruicao' in sys.argv or long
    source=root/rom;dest=root/(rom+('_destruicao_longa' if long else '_destruicao' if destruction else '_ensaios_depurar' if '--depurar' in sys.argv else '_ensaios_piloto' if pilot else '_ensaios'));dest.mkdir(exist_ok=True)
    rows=list(csv.DictReader((source/'preparacao.csv').open()))
    audit={r['modelo']:r for r in json.loads((root/f'auditoria_{rom}.json').read_text(encoding='utf-8'))}
    if destruction:
        with (root/(rom+'_ensaios')/'resultados.csv').open() as stream:proven=list(csv.DictReader(stream))
        eligible={r['modelo'] for r in proven if r['rotina'] in ('alvo','alvo_multisprite','alvo_grande')}
        rows=[r for r in rows if r['modelo'] in eligible]
    ids={'1943h10111':['M005','M008','M011','M018'],'1943h11000':['M006','M009','M012','M019','M109']}[rom]
    jobs=[];missing=[]
    for row in rows:
        state=source/(row['modelo']+'.sta')
        if not state.exists():missing.append(row);continue
        if pilot and row['modelo'] not in ids:continue
        weapons=([16] if rom=='1943h10111' else [80]) if destruction else ROMS[rom] if not pilot else ([0,2,8,16] if rom=='1943h10111' else [0,3,8,80])
        for weapon in weapons+([] if destruction else [-1]):
            if '--depurar' in sys.argv and (row['modelo']!='M011' or weapon!=16):continue
            mode='contato' if weapon==-1 else 'arma'
            case=f"{row['modelo']}_{mode}_{weapon:02X}" if weapon>=0 else row['modelo']+'_contato'
            jobs.append('{id='+quote(case)+',model='+quote(row['modelo'])+',mode='+quote(mode)+',weapon='+str(max(weapon,0))+',checkpoint='+quote(state)+',target='+str(int(row['endereco'],16))+',reference='+str(int(audit[row['modelo']]['referencia'],16))+',output='+quote(dest/case)+'}')
    (dest/'jobs.lua').write_text('return {\n'+',\n'.join(jobs)+'\n}\n',encoding='utf-8')
    (dest/'novos').mkdir(exist_ok=True)
    known=[]
    for row in audit.values():known.append('['+quote(f"L_{row['banco']}_{row['template']}_{row['referencia']}")+']=true')
    if long:
        with (root/(rom+'_destruicao')/'novos_estados.csv').open()as stream:
            for row in csv.DictReader(stream):known.append('['+quote(row['chave'])+']=true')
    (dest/'conhecidos.lua').write_text('return {'+','.join(known)+'}',encoding='utf-8')
    (dest/'sem_save.json').write_text(json.dumps(missing,indent=2),encoding='utf-8')
    args=[str(base/'1943h.exe'),rom,'-noreadconfig','-rompath','roms','-nothrottle','-frameskip','0','-noautoframeskip','-video','none','-sound','none','-noplugins','-nocheat','-skip_gameinfo','-cfg_directory',str(dest/'cfg'),'-autoboot_delay','0','-autoboot_script','capture_scripts/executa_matriz_colisoes.lua']
    with (dest/'mame.log').open('w') as log:
        subprocess.run(args,cwd=base,env=dict(os.environ,DEST=dest.as_posix(),JOBS=(dest/'jobs.lua').as_posix(),ROM=rom,DESTRUCTION='1' if destruction else '0',KNOWN=(dest/'conhecidos.lua').as_posix(),OBSERVE_FRAMES='600'if long else'120'),stdout=log,stderr=subprocess.STDOUT,timeout=3600,check=True,creationflags=subprocess.CREATE_NO_WINDOW)
    print(rom,len(jobs),'ensaios finalizados',flush=True)
if __name__=='__main__':run(sys.argv[1],'--piloto' in sys.argv)
