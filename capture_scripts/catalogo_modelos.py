from pathlib import Path
from collections import Counter,defaultdict
import csv
import json
import struct
import zipfile
import sys
from rotulos_catalogo import EXTRA_FIELDS,decorate

base=Path(__file__).resolve().parents[1]
rom=sys.argv[1]
folder=base/'captures'/rom/'catalogacao_01'
dest=folder/'analise'
dest.mkdir(exist_ok=True)
with zipfile.ZipFile(base/'roms'/f'{rom}.zip') as archive:
    fixed=archive.read('01.12d');banks=archive.read('02.13d')+archive.read('03.14d')

def address_bytes(address,bank,length):
    if address<0x8000:return fixed[address:address+length]
    offset=bank*0x4000+address-0x8000
    return banks[offset:offset+length]

def read_rows(name):
    with (folder/name).open(newline='',encoding='utf-8') as stream:
        for row in csv.DictReader(stream):
            if None in row or any(value is None for value in row.values()):continue
            yield row

phase_events=[(int(row['quadro']),int(row['valor'])) for row in read_rows('eventos.csv') if row['evento']=='fase']
def phase_at(frame):
    phase=0
    for start,value in phase_events:
        if start>frame:break
        phase=value
    return phase+1

models={}
instances={}
for row in read_rows('objetos.csv'):
    if row['tipo']!='nascimento_candidato':continue
    pc=int(row['pc'],16);bank=int(row['banco'])
    if address_bytes(pc-2,bank,2)!=b'\xed\xb0':continue
    template=(int(row['hl'],16)-8)&0xffff
    raw=bytes.fromhex(row['bytes_no_quadro_seguinte'])
    if len(raw)!=32:continue
    reference=struct.unpack_from('<H',raw,28)[0]
    key=(-1 if template<0x8000 else bank,template,reference)
    frame=int(row['quadro'])
    if key not in models:
        name='A identificar'
        if rom=='1943h10111':
            if bank==0 and template==0x88f4:name='Aviao pequeno - formacao inicial'
            if bank==6 and template==0x9ab1:name='Aviao pequeno - formacao vermelha'
            if pc==0x471d:name='Avioes da abertura - verificar papel'
        models[key]={'primeiro':frame,'slot':row['registro'],'instancia':row['instancia'],'nome':name,'fases':set(),'count':0,'graphics':Counter(),'owner_graphics':Counter(),'samples':[],'pcs':set(),'visivel':None}
    model=models[key];model['count']+=1;model['fases'].add(phase_at(frame));model['pcs'].add((bank,pc))
    if len(model['samples'])<4:model['samples'].append((frame,row['registro'],row['instancia']))
    instances[int(row['instancia'])]=(key,frame,int(row['registro'],16))

# A associacao direta usa o ID do registro no momento da transferencia ao video.
# Referencias IX/IY sao preservadas no arquivo original para investigacao de pecas filhas.
for row in read_rows('graficos.csv'):
    instance=int(row['instancia'])
    if instance not in instances:continue
    key,born,slot=instances[instance]
    frame=int(row['quadro'])
    if frame<born or frame-born>600:continue
    x,y=int(row['x']),int(row['y'])
    if -16<x<256 and 0<=y<240:
        models[key]['graphics'][(int(row['codigo'],16),int(row['paleta'],16))]+=1
        if int(row['codigo'],16)!=0 and models[key]['visivel'] is None:models[key]['visivel']=frame

def classify(model):
    graphics=[(code,pal) for (code,pal),count in model['graphics'].most_common() if code!=0]
    if not graphics:return 'Sem grafico associado','Controle ou objeto ainda sem associacao visual'
    graphics=[item for item in graphics if item[1]!=9] or graphics
    code,pal=graphics[0]
    if model['nome'].startswith('Avioes da abertura'):return 'Aviao da abertura',model['nome']
    if model['nome'].startswith('Aviao pequeno'):return 'Aviao pequeno',model['nome']
    if pal in (4,5,6,7) and (0x200<=code<0x2c0 or 0x750<=code<0x760 or 0x7c0<=code<0x7fd):
        return 'Aviao pequeno',f'Aviao pequeno - serie grafica {code&0xff0:03X}'
    if pal in (6,7) and 0x180<=code<0x200:return 'Componente de aviao',f'Peca de aviao - serie {code&0xff0:03X}'
    if pal!=9 and (0x2c0<=code<0x400 or 0x600<=code<0x700):return 'Componente de aviao grande',f'Aviao maior - peca grafica {code:03X}'
    if pal==15 and (0x400<=code<0x5c0 or 0x700<=code<0x740):return 'Canhao',f'Canhao ou torre - serie grafica {code&0xff0:03X}'
    if pal==15 and 0x760<=code<0x780:return 'Base ou componente de canhao',f'Base ou componente de torre - grafico {code:03X}'
    if pal==15 and 0x5c0<=code<0x5e8:return 'Base ou componente de canhao',f'Componente de torre - grafico {code:03X}'
    if pal==10 and 0x180<=code<0x1a0:return 'Componente de barco',f'Peca de embarcacao - grafico {code:03X}'
    if pal==15 and 0x740<=code<0x750:return 'Plataforma',f'Plataforma de embarcacao - grafico {code:03X}'
    if pal==9:return 'Projetil ou efeito',f'Projetil ou efeito - grafico {code:03X}'
    if code<0x50:return 'Jogador ou controle',f'Grafico do jogador/controle - {code:03X}'
    return 'A confirmar',model['nome']

fields=['modelo','rotulo','banco','pc_apos_LDIR','modelo_ROM','referencia_1C','primeiro_quadro','registro_exemplo','instancia_exemplo','fases','ocorrencias','graficos_paletas_observados','amostras','categoria','primeiro_grafico_visivel','imagem_referencia']+EXTRA_FIELDS
catalog_rows=[]
with (dest/'modelos.csv').open('w',encoding='utf-8-sig',newline='') as stream:
    writer=csv.writer(stream);writer.writerow(fields)
    for index,(key,model) in enumerate(sorted(models.items(),key=lambda item:item[1]['primeiro']),1):
        bank,template,reference=key
        graphics=' '.join(f'{code:03X}/p{palette:X}' for (code,palette),count in model['graphics'].most_common(16))
        pcs=' '.join(f'{b}:{pc:04X}' for b,pc in sorted(model['pcs']))
        category,label=classify(model)
        frame=model['visivel'];shot=f'f{((frame+3)//4)*4:07d}.png' if frame is not None else ''
        row=[f'M{index:03d}',label,bank,pcs,f'{template:04X}',f'{reference:04X}',model['primeiro'],model['slot'],model['instancia'],' '.join(map(str,sorted(model['fases']))),model['count'],graphics,json.dumps(model['samples']),category,frame,shot]
        decorated=decorate(dict(zip(fields,row)),rom)
        writer.writerow([decorated[field] for field in fields]);catalog_rows.append(decorated)
with (dest/'avioes_canhoes.csv').open('w',encoding='utf-8-sig',newline='') as stream:
    writer=csv.DictWriter(stream,fieldnames=fields);writer.writeheader()
    writer.writerows(row for row in catalog_rows if 'aviao' in row['categoria'].lower() or 'canhao' in row['categoria'].lower())
print('Categorias:',dict(Counter(row['categoria'] for row in catalog_rows)),flush=True)
print(rom,'modelos LDIR',len(models),'instancias',len(instances),flush=True)
for key,model in list(sorted(models.items(),key=lambda item:item[1]['primeiro']))[:25]:
    print(key,model['nome'],model['primeiro'],model['count'],model['graphics'].most_common(4),flush=True)
