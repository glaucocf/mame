from pathlib import Path
import os
import subprocess
import sys

base=Path(__file__).resolve().parents[1]
global_test='--global' in sys.argv
identified_test='--identified' in sys.argv
for rom,state in [('1943h10111','fase_01_f0010276.sta'),('1943h11000','fase_02_f0149380.sta')]:
    dest=base/'captures'/rom/('identificacoes_verificacao' if identified_test else 'editor_global_verificacao' if global_test else 'editor_objetos_verificacao')
    dest.mkdir(parents=True,exist_ok=True)
    saved=base/'captures'/rom/'campanha/campanha_com_tiro_01'/state
    script='capture_scripts/verifica_identificacoes.lua' if identified_test else 'capture_scripts/verifica_editor_global.lua' if global_test else 'capture_scripts/verifica_editor_objetos.lua'
    args=[str(base/'1943h.exe'),rom,'-noreadconfig','-rompath','roms','-state',str(saved),'-nothrottle','-frameskip','0','-video','none','-sound','none','-skip_gameinfo','-plugins','-plugin','cheat','-cheat','-pluginspath','plugins','-cheatpath','cheat','-cfg_directory',str(dest/'cfg'),'-autoboot_delay','0','-autoboot_script',script]
    with (dest/'mame.log').open('w') as log:
        subprocess.run(args,cwd=base,env=dict(os.environ,DEST=dest.as_posix()),stdout=log,stderr=subprocess.STDOUT,check=True,timeout=60)
    report=(dest/('identificacoes_verificacao.txt' if identified_test else 'global_verificacao.txt' if global_test else 'editor_verificacao.txt')).read_text()
    print(rom,report,flush=True)
    assert 'ERRO' not in report and 'Concluido' in report
