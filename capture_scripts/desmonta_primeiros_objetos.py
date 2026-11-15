from pathlib import Path
import importlib.util
import zipfile
import re

base=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('z80',Path(__file__).with_name('disasm_audio.py'))
decoder=importlib.util.module_from_spec(spec);spec.loader.exec_module(decoder)
decoder.NAMED_ADDRS={}

def instruction(memory,pc):
    mnemonic,length,*_=decoder.decode(memory,pc)
    opcode=memory[pc]
    pairs={0x09:'BC',0x19:'DE',0x29:'HL',0x39:'SP'}
    if opcode in pairs:return 'ADD HL,'+pairs[opcode],1
    if opcode in (0xdd,0xfd):
        register='IX' if opcode==0xdd else 'IY'
        if memory[pc+1] in pairs:
            operand=pairs[memory[pc+1]]
            return 'ADD '+register+','+(register if operand=='HL' else operand),2
        if re.search(r'\(I[XY][+-]\d+\)',mnemonic):
            displacement=memory[pc+2]
            if displacement>=128:displacement-=256
            mnemonic=re.sub(r'\(I[XY][+-]\d+\)',f'({register}{displacement:+d})',mnemonic)
            mnemonic=mnemonic.replace(register+'H','H').replace(register+'L','L')
    return mnemonic,length
with zipfile.ZipFile(base/'roms/1943h10111.zip') as archive:
    memory=archive.read('01.12d')+archive.read('02.13d')[:0x4000]
    bank6=archive.read('01.12d')+archive.read('03.14d')[0x8000:0xc000]
output=['Listagem exploratoria. As faixas incluem dados que podem ser apresentados como instrucoes.\n']
for start,end in [(0x06d0,0x0750),(0x46d0,0x4750),(0x5500,0x5660),(0x5940,0x59c0),(0x59c0,0x5aa0),(0x87b0,0x89b0)]:
    output.append(f'\nROM fixa/banco 0: {start:04X}-{end:04X}\n')
    pc=start
    while pc<end:
        mnemonic,length=instruction(memory,pc)
        output.append(f'{pc:04X}  {memory[pc:pc+length].hex(" "):12}  {mnemonic}\n')
        pc+=length
folder=base/'captures/1943h10111/primeiros_objetos'
(folder/'rotinas_banco0.txt').write_text(''.join(output))
pc=0x9a50
output=[]
while pc<0x9ad0:
    mnemonic,length=instruction(bank6,pc)
    output.append(f'{pc:04X} {bank6[pc:pc+length].hex(" "):12} {mnemonic}\n')
    pc+=length
(folder/'rotina_grupo_banco6.txt').write_text(''.join(output))
print(''.join(output))
