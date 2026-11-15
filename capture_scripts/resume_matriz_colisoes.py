from pathlib import Path
from collections import Counter,defaultdict
import csv,json
base=Path(__file__).resolve().parents[1];root=base/'captures'/'matriz_colisoes_01'
for rom,expected in [('1943h10111',816),('1943h11000',1050)]:
    folder=root/(rom+'_ensaios')
    assert 'estado=concluido' in (folder/'status.txt').read_text()
    rows=list(csv.DictReader((folder/'resultados.csv').open()));assert len(rows)==expected and len({r['caso'] for r in rows})==expected
    grouped=defaultdict(list)
    for row in rows:grouped[row['modelo']].append(row)
    unresolved=[];summary=[]
    for model,items in grouped.items():
        weapons=[r for r in items if r['modo']=='arma'];contact=next(r for r in items if r['modo']=='contato')
        hits=[r for r in weapons if r['resultado'].startswith('atingiu')]
        routines=sorted({r['rotina'] for r in hits})
        flags=int(items[0]['flags_iniciais'],16)
        reason=''
        if flags&2 and len(hits)!=len(weapons):reason='flags permitem tiros, mas existem armas sem acerto'
        if flags&1 and contact['resultado'] not in ('causou_dano_ao_jogador','resposta_de_contato'):reason+=(('; ' if reason else '')+'contato permitido sem resposta confirmada')
        if reason:unresolved.append({'modelo':model,'flags':f'{flags:02X}','motivo':reason,'resultados':dict(Counter(r['resultado'] for r in items))})
        summary.append({'modelo':model,'flags_iniciais':f'{flags:02X}','rotinas':' '.join(routines),'armas_com_acerto':' '.join(r['arma'] for r in hits),'armas_que_continuam':' '.join(r['arma'] for r in hits if r['resultado']=='atingiu_e_continuou'),'resistencia_inicial':items[0]['resistencia_inicial'],'contato':contact['resultado'],'dano_por_contato':contact['dano_por_contato'],'revisao':reason})
    with (root/f'resumo_{rom}.csv').open('w',encoding='utf-8-sig',newline='') as stream:
        writer=csv.DictWriter(stream,fieldnames=list(summary[0]));writer.writeheader();writer.writerows(summary)
    (root/f'revisar_{rom}.json').write_text(json.dumps(unresolved,ensure_ascii=False,indent=2),encoding='utf-8')
    print(rom,len(rows),'casos',len(grouped),'perfis',dict(Counter(r['resultado'] for r in rows)),'revisar',len(unresolved),flush=True)
    for item in unresolved:print(json.dumps(item,ensure_ascii=False),flush=True)
