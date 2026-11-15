"""Valida os XMLs preparados e confirma que os globais sao somente acrescimos."""
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
import re
import subprocess
import xml.etree.ElementTree as ET

base=Path(__file__).resolve().parents[1]
names=['1943.xml','1943kai.xml','1943mii.xml','1943u.xml']+[f'1943h{i:05b}.xml' for i in range(32)]
expected=sorted('cheat/'+name for name in names)
staged=subprocess.check_output(['git','diff','--cached','--name-only'],cwd=base,text=True).splitlines()
assert sorted(staged)==expected,staged

def check(name):
    path='cheat/'+name
    data=subprocess.check_output(['git','show',':'+path],cwd=base).decode('utf-8')
    root=ET.fromstring(data)
    assert root.tag=='mamecheat'
    global_block=re.search(r'<!-- EDITOR GLOBAL BEGIN -->.*?<!-- EDITOR GLOBAL END -->',data,re.S).group()
    items=ET.fromstring('<mamecheat>'+global_block+'</mamecheat>').findall('cheat')
    assert len(items)==8
    for item in items:
        assert item.get('enabled')!='yes'
        declared=int(item.get('tempvariables','10'))
        assert all(int(index)<declared for index in re.findall(r'\btemp(\d+)\b',ET.tostring(item,encoding='unicode')))
    previous='cheat/archived_presets/antes_editor_global_20261114/'+name
    diff=subprocess.run(['git','diff','--no-index','--numstat','--',previous,path],cwd=base,stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True)
    assert diff.returncode==1,(name,diff.stderr)
    added,removed,_=diff.stdout.strip().split('\t',2)
    assert (added,removed)==('10','0'),(name,diff.stdout)
    print(name+' OK',flush=True)
    return global_block

with ThreadPoolExecutor(max_workers=8) as pool:
    blocks=list(pool.map(check,names))
assert all(block==blocks[0] for block in blocks)
whitespace=subprocess.run(['git','diff','--cached','--check'],cwd=base,stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True)
if whitespace.returncode:
    # Estes espacos ja estavam nos templates, agora rastreados pela primeira vez.
    inherited={('cheat/1943mii.xml','89'),('cheat/1943u.xml','89'),('cheat/1943u.xml','107')}
    warnings=set(re.findall(r'^(cheat/[^:]+):(\d+): trailing whitespace\.$',whitespace.stdout,re.M))
    assert whitespace.returncode==2 and warnings==inherited and not whitespace.stderr,whitespace.stdout+whitespace.stderr
    assert all(line==line.rstrip() for line in blocks[0].splitlines())
    print('Tres espacos finais herdados dos templates preservados; nenhum introduzido no bloco global.')
subprocess.run(['git','diff','--exit-code','--',*expected],cwd=base,check=True)
print('36 XMLs preparados e validos; globais identicos; apenas 10 linhas acrescentadas por arquivo; controles individuais integralmente preservados.')
