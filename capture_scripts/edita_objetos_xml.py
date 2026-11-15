"""Acrescenta o editor grafico aos quatro templates e 32 hibridos sem reformatar os cheats existentes."""
from pathlib import Path
import csv
import re
import shutil
from xml.sax.saxutils import escape
import xml.etree.ElementTree as ET
import sys
import subprocess

BASE=Path(__file__).resolve().parents[1]
CHEATS=BASE/'cheat'
START='<!-- EDITOR OBJETOS BEGIN -->'
END='<!-- EDITOR OBJETOS END -->'
GLOBAL_START='<!-- EDITOR GLOBAL BEGIN -->'
GLOBAL_END='<!-- EDITOR GLOBAL END -->'
IDENTIFIED_START='<!-- EDITOR IDENTIFICADOS BEGIN -->'
IDENTIFIED_END='<!-- EDITOR IDENTIFICADOS END -->'
CATALOG=CHEATS/'catalogo_objetos.csv'

def action(text,condition=None):
    attr='' if condition is None else ' condition="'+escape(condition,{'"':'&quot;'})+'"'
    return '<action'+attr+'>'+escape(text)+'</action>'

def script(state,actions):
    return '<script state="'+state+'">'+''.join(actions)+'</script>'

def cheat(name,body,comment,tempvariables=10):
    variables='' if tempvariables==10 else f' tempvariables="{tempvariables}"'
    return '<cheat desc="'+escape(name,{'"':'&quot;'})+'"'+variables+'><comment>'+escape(comment)+'</comment>'+body+'</cheat>'

def parameter(maximum):
    return f'<parameter min="0" max="0x{maximum:X}" step="1"/>'

def mem(address):
    return f'maincpu.pb@{address:04X}'

def build_globals():
    parts=[GLOBAL_START,'<cheat desc="--- EDITOR GLOBAL: todos os 128 registros ---"/>']
    capture=[];freeze=[];set_x=[];set_y=[];graphics=[];palettes=[]
    hide_on=[];hide_run=[];hide_off=[]
    for slot in range(128):
        base=0xf000+slot*32
        code,attr,y,x=[mem(base+i) for i in (0,1,2,3)]
        temp=f'temp{slot}'
        capture.append(action(f'{temp}=maincpu.pw@{base+2:04X}+(({attr} band 10) lshift C)'))
        freeze += [action(f'{x}=({temp} rshift 8) band FF','(param band 1) ne 0'),action(f'{attr}=({attr} band EF) bor (({temp} rshift C) band 10)','(param band 1) ne 0'),action(f'{y}={temp} band FF','(param band 2) ne 0')]
        set_x += [action(f'{x}=param'),action(f'{attr}={attr} band EF')]
        set_y.append(action(f'{y}=param'))
        graphics += [action(f'{code}=param band FF'),action(f'{attr}=({attr} band 1F) bor ((param rshift 3) band E0)')]
        palettes.append(action(f'{attr}=({attr} band F0) bor param'))
        hide_on.append(action(f'{temp}={x}+(({attr} band 10) lshift 8)'))
        hide_run += [action(f'{x}=0'),action(f'{attr}={attr} bor 10')]
        hide_off += [action(f'{x}={temp} band FF'),action(f'{attr}=({attr} band EF) bor (({temp} rshift 8) band 10)')]
    modes='<parameter><item value="1">Travar X de cada registro</item><item value="2">Travar Y de cada registro</item><item value="3">Travar X e Y de cada registro</item></parameter>'
    parts.append(cheat('Editor GLOBAL - travar posicoes atuais',modes+script('on',capture)+script('run',freeze),'Guarda a posicao propria de cada registro ao ligar. Afeta tambem jogador, tiros e efeitos. Desligar libera as atualizacoes. Atua nos campos da tabela grafica.',128))
    for title,maximum,actions,comment in [('X interno',255,set_x,'Fixa o MESMO X interno nos 128 registros, limpando o sinal negativo.'),('Y interno',255,set_y,'Fixa o MESMO Y interno nos 128 registros.'),('grafico generico',0x7ff,graphics,'Aplica o MESMO grafico 000-7FF aos 128 registros; preserva paleta e sinal X.'),('paleta',15,palettes,'Aplica a MESMA paleta 0-F aos 128 registros; preserva os outros atributos.')]:
        parts.append(cheat('Editor GLOBAL - '+title,parameter(maximum)+script('run',actions),comment+' Inclui jogador, tiros, inimigos e efeitos. Desative os controles individuais que escrevem no mesmo campo.'))
    parts.append(cheat('Editor GLOBAL - ocultar todas as pecas',script('on',hide_on)+script('run',hide_run)+script('off',hide_off),'Mantem os 128 registros em X=-256. Ao desligar, restaura o X e sinal proprios de cada registro capturados ao ligar. A partida continua executando.',128))
    copies=[action('temp1=F000+param*20')]
    for slot in range(128):
        for offset in range(32):
            copies.append(action(f'{mem(0xf000+slot*32+offset)}=maincpu.pb@(temp1+{offset:X})'))
    parts.append(cheat('Editor GLOBAL - copiar origem para TODOS (experimental)',parameter(127)+script('change',copies),'Acao unica: escolha a origem 00-7F. Copia seus 32 bytes para TODOS os 128 registros, incluindo jogador e objetos em uso. Pode desorganizar a partida. Use save para restaurar. A copia nao garante inicializacao de inimigos.'))
    parts.append(GLOBAL_END)
    return '\n'.join(parts)+'\n'

def build_identified():
    parts=[IDENTIFIED_START,'<cheat desc="--- REFERENCIAS: fase 1 de 1943h10111 ---"/>']
    items=''.join(f'<item value="0x{slot:02X}">Registro {slot:02X} [{0xf000+slot*32:04X}]</item>' for slot in range(0x2e,0x3e))
    outputs=[]
    for label,fmt,expr in [('Registro pequeno','%02X','param'),('Ocupacao +08 (0=livre)','%02X','maincpu.pb@(F008+param*20)'),('Grupo +07','%02X','maincpu.pb@(F007+param*20)'),('Marca especial +15','%02X','maincpu.pb@(F015+param*20)'),('Contador E200+grupo','%u','maincpu.pb@(E200+maincpu.pb@(F007+param*20))'),('Referencia +1C','%04X','maincpu.pw@(F01C+param*20)'),('Referencia +1E','%04X','maincpu.pw@(F01E+param*20)')]:
        outputs.append(f'<output format="{escape(label)}: {fmt}"><argument>{escape(expr)}</argument></output>')
    parts.append(cheat('Editor - investigar pequenos (ref.1943h10111)','<parameter>'+items+'</parameter><script state="run">'+''.join(outputs)+'</script>','Somente leitura. Na fase 1 de 1943h10111, a rotina 06DF usa o campo +08 para procurar vagas nos 16 registros 2E-3D. Grupo 07 e marca F7 foram relacionados a formacoes vermelhas. O contador de grupos comuns pode dar a volta; interprete o brinde somente com os dados da formacao especial. Outros programas e fases precisam de confirmacao.'))
    groups=''.join(f'<item value="0x{group:X}">Grupo {group:02X} [E2{group:02X}]'+(' - vermelho observado' if group==7 else '')+'</item>' for group in range(16))
    parts.append(cheat('Editor - consultar contador de grupo','<parameter>'+groups+'</parameter><script state="run"><output format="Grupo: %02X  Contador: %u"><argument>param</argument><argument>maincpu.pb@(E200+param)</argument></output></script>','Somente leitura. E207 contou membros do grupo vermelho na fase 1 de 1943h10111: foi incrementado na criacao e decrementado nas destruicoes. Chegar a zero foi seguido pelo bonus. Isso nao estabelece a regra de todos os grupos ou de outras ROMs.'))
    graphics=[(0x208,'Pequeno - quadro 208'),(0x218,'Pequeno - quadro 218'),(0x362,'Abertura - peca 1'),(0x363,'Abertura - peca 2'),(0x36a,'Abertura - peca 3'),(0x36b,'Abertura - peca 4'),(0x640,'Grande - peca 1'),(0x641,'Grande - peca 2'),(0x648,'Grande - peca 3'),(0x649,'Grande - peca 4')]
    options=''.join(f'<item value="0x{code:X}">{name}</item>' for code,name in graphics)
    parts.append(cheat('Editor - referencias graficas identificadas','<parameter>'+options+'</parameter><script state="run"><output format="Grafico de referencia: %03X"><argument>param</argument></output></script>','Catalogo de referencia, somente leitura. Observado em 1943h10111: pequenos 208/218 com paleta 6; abertura 362/363/36A/36B; grande 640/641/648/649 com paleta D. Sao codigos das pecas graficas, nao identificadores de criacao de inimigos. Consulte-os ao ajustar grafico generico nos controles existentes.'))
    parts.append(IDENTIFIED_END)
    return '\n'.join(parts)+'\n'

def build(names,references=None):
    parts=[START,'<cheat desc="--- EDITOR GRAFICO: registros 00-7F ---"/>']
    references=references or ['']*128
    entries=''.join(f'<item value="0x{i:02X}">{escape(name)} [F000+{i*32:03X}]'+(' - '+escape(references[i]) if references[i] else '')+'</item>' for i,name in enumerate(names))
    outputs=[]
    for label,fmt,expr in [('Registro','%02X','param'),('Grafico','%03X','maincpu.pb@(F000+param*20)+((maincpu.pb@(F001+param*20) band E0) lshift 3)'),('Paleta','%X','maincpu.pb@(F001+param*20) band F'),('X interno','%d','maincpu.pb@(F003+param*20)-((maincpu.pb@(F001+param*20) band 10) lshift 4)'),('Y interno','%d','maincpu.pb@(F002+param*20)')]:
        outputs.append(f'<output format="{label}: {fmt}"><argument>{escape(expr)}</argument></output>')
    parts.append(cheat('Editor - consultar registro','<parameter>'+entries+'</parameter><script state="run">'+''.join(outputs)+'</script>','Somente consulta. As entradas incluem jogador, inimigos, tiros e efeitos. Os eixos sao internos ao video antes da rotacao.'))
    for slot,name in enumerate(names):
        base=0xf000+slot*32
        code,attr,y,x=[mem(base+i) for i in (0,1,2,3)]
        prefix=f'Editor {slot:02X} [{base:04X}] {name}'
        parts.append(f'<cheat desc="--- {escape(prefix)} ---"/>')
        modes='<parameter><item value="1">Travar X atual</item><item value="2">Travar Y atual</item><item value="3">Travar X e Y atuais</item></parameter>'
        body=modes+script('on',[action(f'temp0={x}'),action(f'temp1={y}'),action(f'temp2={attr} band 10')])
        body+=script('run',[action(f'{x}=temp0','(param band 1) ne 0'),action(f'{attr}=({attr} band EF) bor temp2','(param band 1) ne 0'),action(f'{y}=temp1','(param band 2) ne 0')])
        parts.append(cheat(prefix+' - travar posicao grafica',body,'Captura as coordenadas ao ligar. Ao desligar, o jogo volta a atualiza-las. Nao congela automaticamente a IA, colisoes ou outras pecas do mesmo inimigo.'))
        parts.append(cheat(prefix+' - X interno',parameter(255)+script('run',[action(f'{x}=param'),action(f'{attr}={attr} band EF')]),'Fixa X de video em 0-255 e retira o sinal negativo. Pode conflitar com travar posicao ou ocultar.'))
        parts.append(cheat(prefix+' - Y interno',parameter(255)+script('run',[action(f'{y}=param')]),'Fixa Y de video em 0-255. A tela do arcade e girada; nao sao os eixos do monitor final.'))
        parts.append(cheat(prefix+' - grafico generico',parameter(0x7ff)+script('run',[action(f'{code}=param band FF'),action(f'{attr}=({attr} band 1F) bor ((param rshift 3) band E0)')]),'Escolhe o codigo grafico 000-7FF. Troca a aparencia desta peca; a rotina do inimigo continua sendo a original.'))
        parts.append(cheat(prefix+' - paleta',parameter(15)+script('run',[action(f'{attr}=({attr} band F0) bor param')]),'Paleta 0-F; preserva extensao do codigo grafico e sinal X.'))
        body=script('on',[action(f'temp0={x}'),action(f'temp1={attr} band 10')])+script('run',[action(f'{x}=0'),action(f'{attr}={attr} bor 10')])+script('off',[action(f'{x}=temp0'),action(f'{attr}=({attr} band EF) bor temp1')])
        parts.append(cheat(prefix+' - ocultar peca',body,'Coloca esta peca em X=-256. Ao desligar restaura X e sinal capturados. A logica do jogo continua executando.'))
        copies=[action('temp1=F000+param*20')]
        # Registros alinhados a 32 bytes sao distintos ou identicos, sem sobreposicao parcial.
        copies += [action(f'maincpu.pb@(temp1+{i:X})={mem(base+i)}') for i in range(32)]
        parts.append(cheat(prefix+' - copiar registro para (experimental)',parameter(127)+script('change',copies),'Acao unica: copia os 32 bytes ao destino 00-7F. Sobrescreve o registro escolhido. Copiar dados nao garante inicializacao completa de um inimigo; use save para restaurar a partida.'))
    parts.extend([END])
    return '\n'.join(parts)+'\n'

def main():
    if not CATALOG.exists():
        with CATALOG.open('w',encoding='utf-8-sig',newline='') as stream:
            writer=csv.writer(stream);writer.writerow(['registro_hex','endereco_hex','nome'])
            writer.writerows((f'{i:02X}',f'{0xf000+i*32:04X}',f'Objeto {i:02X}') for i in range(128))
    with CATALOG.open(encoding='utf-8-sig',newline='') as stream:
        rows=list(csv.DictReader(stream))
    assert [int(row['registro_hex'],16) for row in rows]==list(range(128))
    if 'referencia' not in rows[0]:
        for slot,row in enumerate(rows):
            reference=''
            if 0x2e<=slot<=0x3d:reference='pool pequenos - ref.10111 fase 1'
            if 0x3e<=slot<=0x51:reference='peca da abertura; slot reutilizado - ref.10111'
            if 0x4e<=slot<=0x51:reference='abertura/grande; slot reutilizado - ref.10111'
            row['referencia']=reference
        with CATALOG.open('w',encoding='utf-8-sig',newline='') as stream:
            writer=csv.DictWriter(stream,fieldnames=['registro_hex','endereco_hex','nome','referencia']);writer.writeheader();writer.writerows(rows)
    names=[row['nome'] for row in rows]
    references=[row.get('referencia','') for row in rows]
    block=build(names,references)+build_globals()+build_identified()
    targets=[CHEATS/(name+'.xml') for name in ('1943','1943kai','1943mii','1943u')]
    targets += [CHEATS/f'1943h{i:05b}.xml' for i in range(32)]
    backup=CHEATS/'archived_presets'/'antes_editor_objetos_20261114'
    backup.mkdir(parents=True,exist_ok=True)
    global_backup=CHEATS/'archived_presets'/'antes_editor_global_20261114'
    global_backup.mkdir(parents=True,exist_ok=True)
    identified_backup=CHEATS/'archived_presets'/'antes_identificacoes_20261114'
    identified_backup.mkdir(parents=True,exist_ok=True)
    for path in targets:
        print(path.name,flush=True)
        source=backup/path.name if '--rebuild' in sys.argv and (backup/path.name).exists() else path
        if '--from-head' in sys.argv:
            original=subprocess.check_output(['git','show','HEAD:cheat/'+path.name],cwd=BASE).decode('utf-8')
        else:
            original=source.read_text(encoding='utf-8')
        if IDENTIFIED_START not in original and not (identified_backup/path.name).exists():
            with (identified_backup/path.name).open('w',encoding='utf-8',newline='') as stream:stream.write(original)
        if GLOBAL_START not in original and not (global_backup/path.name).exists():
            if '--rebuild' in sys.argv:
                previous=original.replace('</mamecheat>',build(names)+'</mamecheat>')
                with (global_backup/path.name).open('w',encoding='utf-8',newline='') as stream:stream.write(previous)
            else:
                shutil.copy2(path,global_backup/path.name)
        content=re.sub(re.escape(START)+'.*?'+re.escape(END)+r'\s*','',original,flags=re.S)
        content=re.sub(re.escape(GLOBAL_START)+'.*?'+re.escape(GLOBAL_END)+r'\s*','',content,flags=re.S)
        content=re.sub(re.escape(IDENTIFIED_START)+'.*?'+re.escape(IDENTIFIED_END)+r'\s*','',content,flags=re.S)
        assert content.count('</mamecheat>')==1,path
        updated=content.replace('</mamecheat>',block+'</mamecheat>')
        ET.fromstring(updated)
        if updated==original:continue
        if not (backup/path.name).exists():shutil.copy2(path,backup/path.name)
        temporary=path.with_suffix('.xml.editor_tmp')
        with temporary.open('w',encoding='utf-8',newline='') as stream:stream.write(updated)
        temporary.replace(path)
    print(f'Editor instalado em {len(targets)} XMLs; {len(ET.fromstring("<mamecheat>"+block+"</mamecheat>").findall("cheat"))} entradas novas por XML.')

if __name__=='__main__':main()
