from pathlib import Path
from PIL import Image

root=Path(__file__).resolve().parents[1]/'captures'
for rom,end in (('1943h10111',161530),('1943h00111',166731),('1943h11000',290271)):
    folder=root/rom/'campanha'/'campanha_com_tiro_01'
    frames={int(path.stem[1:]) for path in folder.glob('f*.png')}
    expected=set(range(4,end,4))
    missing=expected-frames
    assert not missing,(rom,sorted(missing)[:20])
    for frame in [4,*range(4000,end,4000),max(expected)]:
        with Image.open(folder/f'f{frame:07d}.png') as image:
            assert image.size==(224,256)
            image.verify()
    print(rom,len(expected),'imagens regulares ate o retorno apos os creditos; sem lacunas de quatro quadros')
