from pathlib import Path
import importlib.util,zipfile,sys
base=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('z80',Path(__file__).with_name('disasm_audio.py'))
decoder=importlib.util.module_from_spec(spec);spec.loader.exec_module(decoder)
decoder.NAMED_ADDRS={}
def instruction(memory,pc):
    op=memory[pc]
    pairs=['BC','DE','HL','SP'];regs=['B','C','D','E','H','L','(HL)','A']
    if op in (9,25,41,57):return 'ADD HL,'+pairs[(op>>4)&3],1
    if op in (0xdd,0xfd):
        r='IX' if op==0xdd else 'IY';sub=memory[pc+1]
        d=memory[pc+2];d=d if d<128 else d-256
        at=f'({r}{d:+d})'
        if sub==0x36:return f'LD {at},${memory[pc+3]:02X}',4
        if sub in (0x34,0x35):return ('INC ' if sub==0x34 else 'DEC ')+at,3
        if 0x40<=sub<0x80 and sub!=0x76 and (sub&7==6 or sub>>3&7==6):
            a=at if sub>>3&7==6 else regs[sub>>3&7];b=at if sub&7==6 else regs[sub&7]
            return f'LD {a},{b}',3
        if 0x80<=sub<0xc0 and sub&7==6:return ['ADD A,','ADC A,','SUB ','SBC A,','AND ','XOR ','OR ','CP '][(sub>>3)&7]+at,3
        if sub in (9,25,41,57):return 'ADD '+r+','+(r if sub==41 else pairs[(sub>>4)&3]),2
    text,length,*_=decoder.decode(memory,pc)
    return text,length

if __name__=='__main__':
    rom,bank,start,end=sys.argv[1:5];bank=int(bank);start=int(start,16);end=int(end,16)
    with zipfile.ZipFile(base/'roms'/f'{rom}.zip') as archive:
        banks=archive.read('02.13d')+archive.read('03.14d')
        memory=archive.read('01.12d')+banks[bank*0x4000:(bank+1)*0x4000]
    pos=start
    while pos<end:
        mnemonic,length=instruction(memory,pos)
        print(f'{pos:04X} {memory[pos:pos+length].hex(" "):14} {mnemonic}')
        pos+=length
