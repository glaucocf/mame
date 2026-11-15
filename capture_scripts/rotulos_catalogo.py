"""Separa aparencia grafica de funcao comprovada no jogo."""
from pathlib import Path
import csv,sys

EXTRA_FIELDS=['engine','conjunto_sprites','funcao_na_engine','evidencia_funcao']
def decorate(row,rom):
    row['engine']='1943' if rom=='1943h10111' else 'Kai'
    row['conjunto_sprites']='Kai' if rom=='1943h10111' else '1943'
    row['funcao_na_engine']='A confirmar: pode ser inimigo, componente, destroco ou efeito'
    row['evidencia_funcao']='Triagem pela aparencia dos graficos; nao comprova funcao'
    key=(str(row['banco']),row['modelo_ROM'],row['referencia_1C'])
    confirmed=rom=='1943h10111' and key in [('0','88F4','5A59'),('6','9AB1','5A59')]
    if confirmed:
        row['funcao_na_engine']='Aviao inimigo pequeno em formacao'
        row['evidencia_funcao']='Formacao inicial ou vermelha observada e rastreada em execucao'
    elif not row['rotulo'].startswith('Visual: '):row['rotulo']='Visual: '+row['rotulo']
    return row

if __name__=='__main__':
    base=Path(__file__).resolve().parents[1]
    for rom in ['1943h10111','1943h11000']:
        for name in ['modelos.csv','avioes_canhoes.csv']:
            path=base/'captures'/rom/'catalogacao_01'/'analise'/name
            with path.open(encoding='utf-8-sig',newline='') as stream:
                reader=csv.DictReader(stream);fields=list(reader.fieldnames);rows=list(reader)
            fields+= [field for field in EXTRA_FIELDS if field not in fields]
            decorated=[decorate(row.copy(),rom) for row in rows]
            assert [row['modelo'] for row in rows]==[row['modelo'] for row in decorated]
            for old,new in zip(rows,decorated):
                assert all(old[field]==new[field] for field in ['banco','modelo_ROM','referencia_1C','primeiro_quadro','graficos_paletas_observados','imagem_referencia'])
            with path.open('w',encoding='utf-8-sig',newline='') as stream:
                writer=csv.DictWriter(stream,fieldnames=fields);writer.writeheader();writer.writerows(decorated)
            print(rom,name,len(rows),'rotulos separados da funcao; dados observados preservados',flush=True)
