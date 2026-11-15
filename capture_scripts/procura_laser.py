from pathlib import Path
import zipfile,importlib.util,sys
base=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('z80',Path(__file__).with_name('disasm_audio.py'))
decoder=importlib.util.module_from_spec(spec);spec.loader.exec_module(decoder)
decoder.NAMED_ADDRS={}
rom=sys.argv[1]
with zipfile.ZipFile(base/'roms'/f'{rom}.zip') as archive:
    fixed=archive.read('01.12d');banks=archive.read('02.13d')+archive.read('03.14d')
memories=[(-1,fixed)]+[(n,fixed+banks[n*0x4000:(n+1)*0x4000]) for n in range(8)]
out=[]
for bank,memory in memories:
    start=0 if bank==-1 else 0x8000
    for pc in range(start,len(memory)-2):
        if memory[pc:pc+3] not in (b'\x32\x51\xf2',b'\x3a\x51\xf2',b'\xdd\x77\x51',b'\xfd\x77\x51',b'\xdd\x36\x51',b'\xfd\x36\x51'):continue
        out.append(f'\nBanco {bank} referencia {pc:04X}\n')
        pos=max(start,pc-40)
        while pos<min(pc+65,len(memory)-4):
            mnemonic,length,*_=decoder.decode(memory,pos)
            out.append(f'{pos:04X} {memory[pos:pos+length].hex(" "):15} {mnemonic}\n');pos+=max(1,length)
    for code in ():
        found=[]
        for pc in range(start,len(memory)-2):
            if memory[pc]==code and memory[pc+1] in range(16):found.append(f'{pc:04X}:{memory[max(start,pc-4):pc+8].hex(" ")}')
        if found:out.append(f'\nCandidato grafico {code:03X} banco {bank}: '+ '; '.join(found)+'\n')
dest=base/'captures'/rom/'catalogacao_01'/'analise'
dest.mkdir(exist_ok=True)
(dest/'rotinas_arma.txt').write_text(''.join(out),encoding='utf-8')
print(''.join(out))
