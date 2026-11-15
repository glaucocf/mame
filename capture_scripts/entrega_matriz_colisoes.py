from pathlib import Path
from collections import Counter,defaultdict
import csv,json,zipfile
base=Path(__file__).resolve().parents[1];root=base/'captures'/'matriz_colisoes_01'
ROMS=['1943h10111','1943h11000']
def read(path):
    with path.open(encoding='utf-8-sig',newline='')as stream:return list(csv.DictReader(stream))
def write(name,rows):
    assert rows,name
    fields=list(dict.fromkeys(field for row in rows for field in row))
    with(root/name).open('w',encoding='utf-8-sig',newline='')as stream:
        w=csv.DictWriter(stream,fieldnames=fields);w.writeheader();w.writerows(rows)
all_rows=[];secondary=[];profiles={};excluded=[];new_objects=[];deaths=[];sources=[]
for rom in ROMS:
    old=read(base/'captures'/rom/'catalogacao_01'/'analise'/'modelos.csv')
    audit={r['modelo']:r for r in json.loads((root/f'auditoria_{rom}.json').read_text(encoding='utf-8'))}
    for row in old:
        item=audit[row['modelo']]
        profiles[(rom,row['modelo'])]={'rom':rom,'modelo':row['modelo'],'origem':'catalogo da campanha','rotulo_visual':row['rotulo'],'banco':item['banco'],'construtor':item['template'],'referencia':item['referencia'],'primeiro_quadro_campanha':item['quadro'],'graficos_observados':row['graficos_paletas_observados']}
    for row in json.loads((root/rom/'excluidos.json').read_text(encoding='utf-8')):excluded.append(dict(row,rom=rom))
    for suffix,prefix in [('_destruicao','N'),('_destruicao_longa','T')]:
        new=read(root/(rom+suffix)/'novos_estados.csv')
        for i,row in enumerate(new,1):
            model=f'{prefix}{i:03d}';item=dict(row,rom=rom,modelo=model,origem='apos morte; causalidade especifica depende da rotina')
            new_objects.append(item)
            if int(row['tipo'],16)&15:
                excluded.append(dict(item,motivo='item/bonus; nao incluido como inimigo, projetil ou destroco'));continue
            parts=row['chave'].split('_')
            profiles[(rom,model)]={'rom':rom,'modelo':model,'origem':'janela de '+('10 segundos apos morte'if prefix=='T'else'2 segundos apos morte'),'rotulo_visual':'Novo perfil: '+row['chave'],'banco':parts[1],'construtor':parts[2],'referencia':row['referencia'],'primeiro_quadro_campanha':'','graficos_observados':'consultar imagem e save do perfil','save':row['arquivo'],'chave':row['chave']}
    for suffix,expected in [('_ensaios',816 if rom=='1943h10111' else 1050),('_ensaios_novos',56 if rom=='1943h10111' else 60),('_ensaios_tardios',8 if rom=='1943h10111' else 10)]:
        folder=root/(rom+suffix);assert 'estado=concluido'in(folder/'status.txt').read_text()
        rows=read(folder/'resultados.csv');assert len(rows)==expected,(folder,len(rows),expected)
        assert len({r['caso']for r in rows})==len(rows)
        all_rows.extend(dict(row,rom=rom,fonte=str(folder/'resultados.csv'))for row in rows);sources.append(folder)
    if rom=='1943h11000':
        for suffix,expected in [('_ensaios_laser_secundario',333),('_ensaios_laser_secundario_tardio',3)]:
            folder=root/(rom+suffix);assert 'estado=concluido'in(folder/'status.txt').read_text()
            rows=read(folder/'resultados.csv');assert len(rows)==expected
            secondary.extend(dict(row,rom=rom,componente='09F',fonte=str(folder/'resultados.csv'))for row in rows);sources.append(folder)
            for event in read(folder/'eventos.csv'):
                if event['tipo']=='grafico_tiro':assert int(event['antes'])==0x09f,event
    for suffix,expected in [('_destruicao',85 if rom=='1943h10111' else 86),('_destruicao_novos',2 if rom=='1943h10111' else 1),('_destruicao_longa',85 if rom=='1943h10111' else 86)]:
        folder=root/(rom+suffix);assert 'estado=concluido'in(folder/'status.txt').read_text()
        rows=read(folder/'resultados.csv');assert len(rows)==expected
        assert all(r['resultado']=='destruido_observado'for r in rows),folder
        deaths.extend(dict(row,rom=rom,observacao_quadros=600 if suffix.endswith('longa') else 120)for row in rows);sources.append(folder)
    # Os novos alvos atingiveis, destruidos outra vez, nao criaram perfis adicionais.
    assert not read(root/(rom+'_destruicao_novos')/'novos_estados.csv')

assert len(all_rows)==2000 and len(secondary)==336 and len(deaths)==345
grouped=defaultdict(list)
for row in all_rows:grouped[(row['rom'],row['modelo'])].append(row)
assert len(grouped)==222
for key,items in grouped.items():
    assert len({(r['flags_iniciais'],r['resistencia_inicial'],r['referencia_inicial'])for r in items})==1,(key,'estado inicial variou')
for row in all_rows+secondary:assert row['referencia_inicial']==row['referencia_esperada'],row
primary={(r['rom'],r['modelo'],r['arma']):r for r in all_rows if r['modo']=='arma'}
for row in secondary:
    original=primary[(row['rom'],row['modelo'],row['arma'])]
    if original['resultado'].startswith('atingiu')and original['rotina']!='projetil':assert row['resultado'].startswith('atingiu'),row
impact_checks=0;arithmetic_review=[]
for row in all_rows+secondary:
    hp=int(row['resistencia_inicial']);after=int(row['resistencia_final']);force=int(row['forca_inicial']);remaining=int(row['forca_final'])
    if row['resultado'].startswith('atingiu'):
        impact_checks+=1
        valid=True
        if row['rotina']=='projetil':
            valid=after==0
            expected='atingiu_e_continuou'if force>hp else'atingiu_e_consumiu_tiro'
            valid=valid and row['resultado']==expected
            if force>hp:valid=valid and remaining==force-hp
        elif row['resultado']=='atingiu_e_continuou':valid=after==0 and remaining==force-hp
        else:valid=after==max(0,hp-force)
        if not valid:arithmetic_review.append(row)
        if row.get('componente')=='09F':assert force==2,row
    if row['modo']=='contato':
        assert int(row['invuln_final'])==0,row
        assert int(row['dano_por_contato'])==int(row['energia_antes_dano'])-int(row['energia_apos_dano']),row

(root/'REVISAR_ARITMETICA.json').write_text(json.dumps(arithmetic_review,indent=2,ensure_ascii=False),encoding='utf-8')
if arithmetic_review:
    print('Casos para repetir:',len(arithmetic_review),flush=True)
    for r in arithmetic_review:print(r['rom'],r['caso'],r['resistencia_inicial'],r['resistencia_final'],r['forca_inicial'],r['forca_final'],flush=True)
    raise SystemExit(1)

catalog=[];contact=[];review=[];projectiles=[]
for key,items in grouped.items():
    info=profiles[key];weapons=[r for r in items if r['modo']=='arma'];touch=next(r for r in items if r['modo']=='contato')
    hits=[r for r in weapons if r['resultado'].startswith('atingiu')];routines=sorted({r['rotina']for r in hits})
    flags=int(items[0]['flags_iniciais'],16)
    if flags&2 and len(hits)!=len(weapons):review.append((key,'arma sem acerto apesar de flag ativa'))
    if flags&1 and touch['resultado']not in('causou_dano_ao_jogador','resposta_de_contato'):review.append((key,'contato sem confirmacao'))
    role='projetil hostil'if'projetil'in routines else'alvo composto grande'if'alvo_grande'in routines else'alvo de multiplas pecas'if'alvo_multisprite'in routines else'objeto atingivel'if'alvo'in routines else'sem colisao direta observada no estado ensaiado'
    item=dict(info,funcao_por_execucao=role,rotinas=' '.join(routines),flags_iniciais=f'{flags:02X}',valor_0B_inicial=items[0]['resistencia_inicial'],armas_com_acerto=' '.join(r['arma']for r in hits),armas_que_continuaram=' '.join(r['arma']for r in hits if r['resultado']=='atingiu_e_continuou'),contato=touch['resultado'],dano_contato=touch['dano_por_contato'])
    catalog.append(item);contact.append(dict(info,resultado=touch['resultado'],energia_antes=touch['energia_antes_dano'],energia_depois=touch['energia_apos_dano'],dano=touch['dano_por_contato'],invuln=touch['invuln_final']))
    if role=='projetil hostil':projectiles.append(item)
assert not review,review
write('MATRIZ_ARMAS.csv',all_rows)
write('MATRIZ_LASER_09F.csv',secondary)
write('CATALOGO_FUNCIONAL.csv',catalog)
write('CONTATO_JOGADOR.csv',contact)
write('PROJETEIS_HOSTIS.csv',projectiles)
write('OBJETOS_APOS_MORTE.csv',new_objects)
write('EXCLUIDOS.csv',excluded)
write('DESTRUICOES.csv',deaths)

validation={'casos_impacto_e_contato':len(all_rows)+len(secondary),'casos_principais':len(all_rows),'casos_laser_09F':len(secondary),'perfis_testados':len(grouped),'destruicoes':len(deaths),'perfis_adicionais_descobertos':len(new_objects),'perfis_adicionais_em_matriz':len(new_objects)-sum(int(r['tipo'],16)&15!=0 for r in new_objects),'impactos_com_aritmetica_conferida':impact_checks,'estado_inicial_identico_por_perfil':True,'referencias_de_perfil_conferidas':True,'pendencias_em_flags_ativas':review,'observacao_pos_morte_quadros':[120,600],'categorias':dict(Counter(r['resultado']for r in all_rows+secondary)),'contatos_com_dano':sum(int(r['dano'])>0 for r in contact),'perfis_projeteis':len(projectiles)}
(root/'VALIDACAO.json').write_text(json.dumps(validation,indent=2,ensure_ascii=False),encoding='utf-8')
report=['# Matriz controlada de colisões — 1943 e Kai\n',
f"Foram concluídos **{validation['casos_impacto_e_contato']} ensaios de impacto/contato em {len(grouped)} perfis** e **{len(deaths)} destruições observadas**. Os perfis incluem inimigos, projéteis, componentes e efeitos; essa contagem não equivale a espécies de inimigos. Os dois conjuntos são 1943h10111 (engine 1943, sprites Kai) e 1943h11000 (engine Kai, sprites 1943).\n",
'## Resultados principais\n',
'Nos projéteis hostis que usam a rotina própria identificada, Shot Gun 02 e 03 fazem a interceptação. Os demais valores de arma testados não entram no teste espacial dessa rotina. Objetos que usam a rotina comum de alvo são uma categoria diferente: podem receber todas as armas e alguns também causam dano por contato. Não se deve classificar um objeto pela aparência do sprite.\n',
'Quando o alvo comum, composto ou grande tem energia menor que a força do componente que o atinge, ele é destruído e o componente continua com a diferença. Quando a energia é igual ou maior, o componente é consumido. Na rotina dos projéteis hostis, o projétil hostil é anulado no encontro aceito, mesmo quando seu campo 0B é maior que a força do tiro; esse campo não deve ser chamado indiscriminadamente de energia.\n',
'O componente 09F dos lasers Kai tem força 2 nos três níveis. Foram feitos 336 ensaios próprios desse componente, separadamente da peça 096, cuja força inicial é 3, 4 ou 5. Os códigos 10, 30 e 50 continuam sujeitos à mesma seleção de colisão contra os projéteis hostis, pois não possuem o bit de arma usado pelos Shot Guns.\n',
'O perfil Kai M109 (construtor banco 4:8392, referência 5B6A), encontrado na sequência após destruição de canhão, recebeu todas as armas. Tem valor 0B 4 e retirou 32 pontos de energia por contato. O perfil clássico N003 usa o construtor correspondente 4:8392, referência 5A59, e também causou 32. O clássico N004, construtor 4:83B2, causou 8. A designação visual específica desses fragmentos pode ser revisada com as imagens e rotinas.\n',
'## Arquivos para consulta\n',
'- [CATALOGO_FUNCIONAL.csv](CATALOGO_FUNCIONAL.csv): um registro por perfil, função determinada pela rotina, construtor, referência, armas com acerto e dano por contato.\n- [MATRIZ_ARMAS.csv](MATRIZ_ARMAS.csv): 2.000 casos principais, com força, estado do tiro, valor do alvo antes/depois e PC da primeira interação.\n- [MATRIZ_LASER_09F.csv](MATRIZ_LASER_09F.csv): 336 casos do segundo componente dos lasers.\n- [CONTATO_JOGADOR.csv](CONTATO_JOGADOR.csv): contato com invencibilidade desligada para os 222 perfis.\n- [PROJETEIS_HOSTIS.csv](PROJETEIS_HOSTIS.csv): perfis confirmados pela rotina própria de projéteis.\n- [OBJETOS_APOS_MORTE.csv](OBJETOS_APOS_MORTE.csv): 16 perfis adicionais observados nas janelas posteriores às mortes; um é item/bonus, fora da matriz de combate. A janela temporal sozinha não prova que cada nascimento foi causado pela morte.\n- [DESTRUICOES.csv](DESTRUICOES.csv), [EXCLUIDOS.csv](EXCLUIDOS.csv) e [VALIDACAO.json](VALIDACAO.json): cobertura e conferência.\n',
'Os diretórios de ensaios preservam resultados brutos e eventos com endereço, valor anterior/posterior, PC, IX e IY. Os diretórios de destruição preservam nascimentos, banco, construtor, pilha, saves e imagens dos novos perfis.\n',
'## Como os ensaios foram isolados\n',
'Cada caso restaurou o mesmo save do perfil. Foram limpos os botões e os tiros anteriores antes da CPU voltar a executar. A arma e seu tempo foram selecionados como nos cheats existentes. As coordenadas foram aproximadas durante a leitura da caixa de colisão, respeitando os centros diferentes das rotinas simples, compostas e grandes. As flags, o valor do alvo e a força do componente não foram alterados para forçar um acerto.\n',
'Nos pontos conhecidos de decisão de colisão, as interações de objetos não selecionados foram suprimidas. Durante os dois quadros de preparação, o alvo também ficou protegido nessas leituras; suas flags na RAM foram preservadas e voltaram a ser usadas normalmente no ensaio ativo. Foi observado o reaproveitamento do registro, para não atribuir ao alvo original a interação com um objeto substituto. Para contato, a energia começou em 64 e F214 ficou em zero após a preparação. O dano informado usa o valor imediatamente anterior e posterior à escrita feita pela rotina do próprio alvo. A força após impacto vem da escrita dessa colisão, não de um quadro posterior em que o projétil poderia ter saído da tela.\n',
'A observação após as mortes usou primeiro 120 e depois 600 quadros, sem frameskip. Os novos objetos atingíveis foram destruídos novamente; nesse segundo ciclo curto não surgiram perfis adicionais desconhecidos. A observação longa encontrou ainda dois controladores tardios de explosão, que receberam sua própria rodada de testes.\n',
'## Limites de interpretação\n',
'Este é um ensaio do efeito de uma colisão no estado salvo. Não é uma medição de alcance, velocidade ou formato exato da caixa em voo natural. Objetos com flags de colisão inativas, jogador ainda sem controle ou ausência de tiro ativo têm esse resultado explicitamente registrado; não foram chamados de imunes. Os estados futuros de um controlador não são demonstrados por um único save.\n',
'O campo 0B pode representar energia, peso/dano de projétil ou um valor de controle, conforme a rotina. Os nomes brutos resistencia_inicial/final foram conservados nos arquivos para rastreabilidade. Cada estado de arma, escudo, jogador 2, dificuldade e ramo secreto adicional pode exigir ensaio próprio. Não foi alterado o programa das ROMs nem acrescentado cheat às XMLs nesta etapa.\n']
(root/'LEIA_ME.md').write_text('\n'.join(report),encoding='utf-8')
deliver=['LEIA_ME.md','MATRIZ_ARMAS.csv','MATRIZ_LASER_09F.csv','CATALOGO_FUNCIONAL.csv','CONTATO_JOGADOR.csv','PROJETEIS_HOSTIS.csv','OBJETOS_APOS_MORTE.csv','EXCLUIDOS.csv','DESTRUICOES.csv','VALIDACAO.json','PLANO.md']
with zipfile.ZipFile(root/'matriz_colisoes.zip','w',zipfile.ZIP_DEFLATED,compresslevel=6)as archive:
    for name in deliver:archive.write(root/name,name)
    for folder in sources:
        for name in ['resultados.csv','eventos.csv','nascimentos.csv','novos_estados.csv','status.txt']:
            path=folder/name
            if path.exists():archive.write(path,path.relative_to(root).as_posix())
with zipfile.ZipFile(root/'matriz_colisoes.zip')as archive:assert archive.testzip()is None
print(json.dumps(validation,ensure_ascii=False,indent=2),flush=True)
