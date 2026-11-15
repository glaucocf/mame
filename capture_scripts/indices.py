from pathlib import Path
for mode in ('obj','chr'):
    a,b,c=[(Path('captures/1943h10111')/mode/f'v{n}.bin').read_bytes() for n in (90,115,135)]
    for i in range(len(a)):
        if a[i]!=b[i] or b[i]!=c[i]:print(mode,hex(0xd000+i),hex(a[i]),hex(b[i]),hex(c[i]))
