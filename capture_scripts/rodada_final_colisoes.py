from pathlib import Path
import subprocess,sys
base=Path(__file__).resolve().parents[1];rom=sys.argv[1]
commands=[['executa_matriz_colisoes.py',rom],['matriz_novos_objetos.py',rom],['matriz_novos_objetos.py',rom,'--longos']]
if rom=='1943h11000':commands+=[['matriz_laser_secundario.py'],['matriz_laser_secundario.py','--tardios']]
for command in commands:
    subprocess.run([sys.executable,str(base/'capture_scripts'/command[0]),*command[1:]],cwd=base,check=True)
print(rom,'rodada final completa com isolamento desde o primeiro quadro',flush=True)
