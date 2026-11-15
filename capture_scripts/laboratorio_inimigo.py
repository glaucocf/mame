"""Prepare and run one native small fighter in the existing MAME build."""
from pathlib import Path
import argparse
import csv
import json
import os
import subprocess
import re

BASE = Path(__file__).resolve().parents[1]
ROOT = BASE / 'captures' / 'laboratorio_inimigos_01'


def prepare(rom, automatic, model=None, short=False):
    if model:
        root = ROOT/'catalogo_isolado'/rom
        profiles = json.loads((root/'jobs.json').read_text(encoding='utf-8'))
        job = next(j for j in profiles if j['id'] == model)
        checkpoint = Path(job['checkpoint'])
        if not checkpoint.exists():
            saved_path = job['checkpoint'].replace('\\', '/')
            assert '/captures/' in saved_path, saved_path
            checkpoint = BASE/'captures'/saved_path.split('/captures/', 1)[1]
        assert checkpoint.exists(), checkpoint
        dest = root/model/('verificacao_inicio' if short else 'verificacao_manual' if automatic else 'sessao')
        dest.mkdir(parents=True, exist_ok=True)
        config = dict(rom=rom, model=model, target=job['target'], reference=job['reference'],
                      hp=job['hp'], routine=job['routine'], engine=int(rom[6]),
                      checkpoint=checkpoint, dest=dest, automatic=automatic,
                      frames=45 if short else 720 if automatic else 0)
        return write_config(dest, config)
    native = ROOT / 'bases' / rom / 'alvo.json'
    if native.exists():
        metadata = json.loads(native.read_text(encoding='utf-8'))
        dest = ROOT / rom / ('verificacao' if automatic else 'sessao')
        dest.mkdir(parents=True, exist_ok=True)
        config = dict(rom=rom, model='aviao_inicial', target=metadata['target'],
                      reference=metadata['reference'], engine=metadata['engine'],
                      checkpoint=native.parent/'aviao_inicial.sta', dest=dest,
                      automatic=automatic, frames=720 if automatic else 0)
        return write_config(dest, config)
    model = 'M005' if rom == '1943h10111' else 'M006'
    source = BASE / 'captures' / 'matriz_colisoes_01' / rom
    with (source / 'preparacao.csv').open(encoding='utf-8') as f:
        row = next(r for r in csv.DictReader(f) if r['modelo'] == model)
    checkpoint = source / f'{model}.sta'
    assert checkpoint.exists()
    dest = ROOT / rom / ('verificacao' if automatic else 'sessao')
    dest.mkdir(parents=True, exist_ok=True)
    config = dict(rom=rom, model=model, target=int(row['endereco'], 16),
                  reference=int(row['referencia_1C'], 16), checkpoint=checkpoint,
                  dest=dest, engine=int(rom[6]), automatic=automatic, frames=720 if automatic else 0)
    return write_config(dest, config)


def write_config(dest, config):
    cfgdir = dest/'cfg'
    cfgdir.mkdir(exist_ok=True)
    for name in ('default', config['rom']):
        cfgfile = cfgdir/(name+'.cfg')
        if not cfgfile.exists():
            cfgfile.write_text(f'<mameconfig version="10"><system name="{name}"/></mameconfig>\n', encoding='utf-8')
    def lua(v):
        if isinstance(v, bool):
            return str(v).lower()
        if isinstance(v, int):
            return str(v)
        return json.dumps(str(v).replace('\\', '/'), ensure_ascii=False)
    path = dest / 'config.lua'
    path.write_text('return {\n' + ',\n'.join(f'{k}={lua(v)}' for k, v in config.items())
                    + '\n}\n', encoding='utf-8')
    return dest, path


def command(rom, dest, automatic):
    local_paths = []
    for option, directory in [('artpath','artwork'),('ctrlrpath','ctrlr'),
                              ('nvram_directory','nvram'),('state_directory','sta'),
                              ('snapshot_directory','snaps')]:
        folder = dest/directory
        folder.mkdir(exist_ok=True)
        local_paths += ['-'+option, str(folder)]
    return [str(BASE / '1943h.exe'), rom, '-noreadconfig', '-rompath',
            'captures/laboratorio_inimigos_01/roms_suporte;roms',
            '-frameskip', '0', '-noautoframeskip', '-noplugins', '-nocheat',
            '-skip_gameinfo', '-cfg_directory', str(dest / 'cfg'), *local_paths,
            '-autoboot_delay', '0', '-autoboot_script', 'capture_scripts/laboratorio_inimigo.lua',
            *(['-nothrottle', '-video', 'none', '-sound', 'none'] if automatic else
              ['-throttle', '-window', '-nomaximize', '-resolution', '672x768'])]


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('rom', nargs='?', default='1943h10111')
    parser.add_argument('--verificar', action='store_true')
    parser.add_argument('--verificar-camadas', action='store_true')
    parser.add_argument('--abrir', action='store_true')
    parser.add_argument('--modelo')
    args = parser.parse_args()
    assert re.fullmatch(r'1943h[01]{5}', args.rom), args.rom
    automatic = args.verificar or args.verificar_camadas
    dest, config = prepare(args.rom, automatic, args.modelo)
    env = dict(os.environ, LAB_CONFIG=str(config), DEST=str(dest).replace('\\', '/'))
    log = (dest / ('mame_camadas.log' if args.verificar_camadas else 'mame.log')).open('w', encoding='utf-8')
    kwargs = dict(cwd=BASE, env=env, stdout=log, stderr=subprocess.STDOUT,
                  creationflags=subprocess.CREATE_NO_WINDOW)
    if args.abrir:
        process = subprocess.Popen(command(args.rom, dest, False), **kwargs)
        (dest / 'processo.json').write_text(json.dumps(dict(pid=process.pid, rom=args.rom)), encoding='utf-8')
        print(f'Sessao aberta: {args.rom}, PID {process.pid}, {dest}')
    else:
        cmd = command(args.rom, dest, automatic)
        if args.verificar_camadas:
            (dest / 'camadas_xml_ok.txt').unlink(missing_ok=True)
            cmd[cmd.index('capture_scripts/laboratorio_inimigo.lua')] = 'capture_scripts/verifica_camadas_xml.lua'
        subprocess.run(cmd, timeout=120 if automatic else None, check=True, **kwargs)
        if args.verificar_camadas:
            assert (dest / 'camadas_xml_ok.txt').exists(), (dest / 'camadas_xml.csv').read_text()
        print(f'Concluido: {dest}')
