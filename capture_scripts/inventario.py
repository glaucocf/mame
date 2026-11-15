from pathlib import Path
import csv
from PIL import Image
root=Path(__file__).resolve().parents[1]/'captures'
with (root/'indice.csv').open('w',encoding='utf-8-sig',newline='') as fp:
 w=csv.writer(fp);w.writerow(['ROM','teste','arquivo','quadro','UPPER','LOWER','paleta','pagina_ou_banco'])
 for rom in ('1943h10111','1943h11000'):
  for mode in ('upper_lower','upper_only','lower_only','object_test','vram_character_code'):
   folder=root/rom/mode
   lines=(folder/'quadros.txt').read_text().splitlines()
   scroll=mode in ('upper_lower','upper_only','lower_only')
   expected=([f'{x:04X}.png' for x in [*range(0,65536,128),65535]] if scroll else
     [f'pal_{p:02X}/sprite_{s:03X}.png' for p in range(16) for s in range(0,2048,64)] if mode=='object_test' else
     [f'pal_{p:02X}/banco_{s:03X}.png' for p in range(32) for s in range(8)])
   assert [line.split(',')[0] for line in lines]==expected
   for line in lines:
    name,frame,*pos=line.split(',')
    path=folder/name
    with Image.open(path) as im:
     assert im.size==(224,256)
     im.verify()
    pal,bank=('','') if scroll else (path.parent.name[4:],path.stem.split('_')[1])
    w.writerow([rom,mode,path.relative_to(root).as_posix(),frame,*(pos or ['','']),pal,bank])
   print(rom,mode,len(lines))
with (root/'aviso_service_test.csv').open('w',encoding='utf-8-sig',newline='') as fp:
 w=csv.writer(fp);w.writerow(['ROM','primeiro_aviso','ultimo_aviso','primeiro_titulo','quadros_visiveis'])
 for rom,a,t in [('1943h10111',26,87),('1943h11000',35,96),('1943h00111',26,86),('1943h01000',122,182)]:
  w.writerow([rom,a,t-1,t,t-a])
