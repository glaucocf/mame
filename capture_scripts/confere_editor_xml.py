from pathlib import Path
import re
import xml.etree.ElementTree as ET
from concurrent.futures import ThreadPoolExecutor
import subprocess

root=Path(__file__).resolve().parents[1]/'cheat'
backup=root/'archived_presets/antes_editor_objetos_20261114'
files=[root/f'{name}.xml' for name in ('1943','1943kai','1943mii','1943u')]
files += [root/f'1943h{i:05b}.xml' for i in range(32)]
def check_file(path):
    text=subprocess.check_output(['cmd.exe','/d','/c','type',str(path.relative_to(root.parent))],cwd=root.parent).decode('utf-8')
    block=re.search(r'<!-- EDITOR OBJETOS BEGIN -->.*?<!-- EDITOR OBJETOS END -->',text,re.S).group()
    old=ET.parse(backup/path.name).getroot().findall('cheat')
    new=ET.fromstring(text).findall('cheat')
    def normalized(node):
        for element in node.iter():
            element.text=(element.text or '').strip()
            element.tail=''
        if node.get('desc')=='Editor - consultar registro':
            for item in node.findall('parameter/item'):item.text=''
        return ET.tostring(node)
    assert [normalized(c) for c in new[:len(old)]]==[normalized(c) for c in old],path.name
    assert len(new)-len(old)==1038,path.name
    assert all(c.get('enabled')!='yes' for c in new[len(old):])
    for entry in new[len(old):]:
        maximum=int(entry.get('tempvariables','10'))
        assert all(int(index)<maximum for index in re.findall(r'\btemp(\d+)\b',ET.tostring(entry,encoding='unicode'))),entry.get('desc')
    previous=ET.parse(root/'archived_presets/antes_editor_global_20261114'/path.name).getroot().findall('cheat')
    assert [normalized(c) for c in new[:len(previous)]]==[normalized(c) for c in previous],path.name
    assert len(new)-len(previous)==12
    identified=re.search(r'<!-- EDITOR IDENTIFICADOS BEGIN -->.*?<!-- EDITOR IDENTIFICADOS END -->',text,re.S).group()
    assert not ET.fromstring('<mamecheat>'+identified+'</mamecheat>').findall('.//action')
    global_block=re.search(r'<!-- EDITOR GLOBAL BEGIN -->.*?<!-- EDITOR GLOBAL END -->',text,re.S).group()
    print(path.name+' OK',flush=True)
    return block,global_block

with ThreadPoolExecutor(max_workers=12) as pool:
    results=list(pool.map(check_file,files))
assert all(result==results[0] for result in results)
print('36 XMLs validos; cheats anteriores e individuais preservados; 8 entradas globais e 4 de identificacao por XML; consultas identificadas somente leitura; novas entradas desligadas.')
