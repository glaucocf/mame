from pathlib import Path
import csv

root=Path(__file__).resolve().parents[1]/'captures'
records=[]
for rom in ('1943h10111','1943h00111','1943h11000'):
    folder=root/rom/'campanha'/'campanha_com_tiro_01'
    rows=list(csv.DictReader((folder/'eventos.csv').read_text().splitlines()))
    first={}
    end=None
    seen_last=False
    for row in rows:
        frame=int(row['quadro']);stage=int(row['fase_E450'])
        if row['evento']=='fase':
            if stage==15:seen_last=True
            if seen_last and stage==0:
                end=frame;break
            if stage<16 and stage not in first:first[stage]=row
    for stage,row in sorted(first.items()):
        start=int(row['quadro'])
        stop=int(first[stage+1]['quadro']) if stage+1 in first else end or int(rows[-1]['quadro'])
        sounds=sorted({r['valor'] for r in rows if r['evento']=='som' and start<=int(r['quadro'])<stop and 0x20<=int(r['valor'],16)<=0x34})
        protections=sum(r['evento']=='protecao_energia' and start<=int(r['quadro'])<stop for r in rows)
        records.append([rom,stage+1,start,stop,row['tanque_E12F'],' '.join(sounds),protections,folder.relative_to(root).as_posix()])
    print(rom,'fases',len(first),'retorno_apos_final',end,'quadros',rows[-1]['quadro'])
with (root/'campanhas_fases.csv').open('w',encoding='utf-8-sig',newline='') as stream:
    writer=csv.writer(stream)
    writer.writerow(['ROM','fase_1_a_16','primeiro_quadro_ID','proximo_ID_ou_retorno','tanque_na_mudanca','comandos_som_20_a_34','intervencoes_energia','pasta'])
    writer.writerows(records)
