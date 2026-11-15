from pathlib import Path
import csv,json,subprocess,os,sys
base=Path(__file__).resolve().parents[1];root=base/'captures'/'matriz_colisoes_01'
def quoted(value):return json.dumps(str(value).replace('\\','/'),ensure_ascii=False)
def prepare(rom,pilot=False):
    audit=json.loads((root/f'auditoria_{rom}.json').read_text(encoding='utf-8'))
    final_start=219070 if rom=='1943h10111' else 347250
    selected=[];excluded=[]
    for row in audit:
        reason=''
        if int(row['slot'],16) in range(0x10,0x1c):reason='jogador'
        elif row['quadro']<600:reason='introducao anterior ao controle'
        elif row['quadro']>=final_start:reason='encerramento'
        elif row['tipo_0A']&15:reason='item ou controle especial; nao classificado como inimigo'
        if reason:excluded.append(dict(row,motivo=reason));continue
        selected.append(row)
    if pilot:
        ids=['M005','M008','M018'] if rom=='1943h10111' else ['M006','M009','M019','M109']
        selected=[row for row in selected if row['modelo'] in ids]
    dest=root/(rom+('_piloto' if pilot else ''));dest.mkdir(exist_ok=True)
    jobs=[]
    for row in selected:
        checkpoint=(row['quadro']-1)//600*600
        state=base/'captures'/rom/'catalogacao_01'/f'checkpoint_f{checkpoint:07d}.sta'
        assert state.exists(),state
        original_fire=row['quadro']>=(215817 if rom=='1943h10111' else 343991)
        jobs.append('{id='+quoted(row['modelo'])+',template='+str(int(row['template'],16))+',bank='+str(row['banco'])+',reference='+str(int(row['referencia'],16))+',checkpoint='+quoted(state)+',baseframe='+str(checkpoint)+',firstframe='+str(row['quadro'])+',originalfire='+str(original_fire).lower()+',output='+quoted(dest/row['modelo'])+'}')
    (dest/'jobs.lua').write_text('return {\n'+',\n'.join(jobs)+'\n}\n',encoding='utf-8')
    (dest/'excluidos.json').write_text(json.dumps(excluded,ensure_ascii=False,indent=2),encoding='utf-8')
    args=[str(base/'1943h.exe'),rom,'-noreadconfig','-rompath','roms','-nothrottle','-frameskip','0','-noautoframeskip','-video','none','-sound','none','-noplugins','-nocheat','-skip_gameinfo','-cfg_directory',str(dest/'cfg'),'-autoboot_delay','0','-autoboot_script','capture_scripts/prepara_matriz_colisoes.lua']
    with (dest/'mame.log').open('w') as log:
        subprocess.run(args,cwd=base,env=dict(os.environ,DEST=dest.as_posix(),JOBS=(dest/'jobs.lua').as_posix()),stdout=log,stderr=subprocess.STDOUT,check=True,timeout=1800,creationflags=subprocess.CREATE_NO_WINDOW)
    print(rom,'preparacao finalizada',len(selected),'perfis',flush=True)
if __name__=='__main__':
    rom=sys.argv[1];prepare(rom,'--piloto' in sys.argv)
