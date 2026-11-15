"""Repackage existing local ROM bytes and create matching lab launchers.

Existing ZIPs are preserved. No program bytes are patched by this script.
"""
from pathlib import Path
import csv
import hashlib
import json
import os
import subprocess
import xml.etree.ElementTree as ET
import zipfile

BASE = Path(__file__).resolve().parents[1]
ROOT = BASE / 'captures' / 'laboratorio_inimigos_01'


def definitions():
    p = subprocess.run([str(BASE/'1943h.exe'), '-listxml', '1943h?????'],
                       cwd=BASE, capture_output=True, check=True,
                       creationflags=subprocess.CREATE_NO_WINDOW)
    machines = {m.get('name'): m for m in ET.fromstring(p.stdout).findall('machine')
                if m.get('name', '').startswith('1943h') and len(m.get('name')) == 10}
    assert len(machines) == 32, len(machines)
    return machines


def build_missing_roms():
    machines = definitions()
    index = {}
    # These five complete sets contain all combinations. Avoid unrelated old
    # letter-named archives, some of which are unavailable OneDrive placeholders.
    sources = [BASE/'roms'/f'{name}.zip' for name in
               ['1943h00111','1943h01000','1943h10111','1943h11000']]
    sources.append(BASE.parent/'1943mii.zip')
    for path in sources:
        with zipfile.ZipFile(path) as archive:
            for info in archive.infolist():
                if not info.is_dir():
                    index.setdefault((f'{info.CRC:08x}', info.file_size), (path, info.filename))
    pending = {}
    for name, machine in sorted(machines.items()):
        if (BASE/'roms'/f'{name}.zip').exists():
            continue
        files = {}
        for r in machine.findall('rom'):
            if r.get('status') == 'nodump':
                continue
            key = (r.get('crc'), int(r.get('size')))
            assert key in index, (name, r.attrib)
            source, filename = index[key]
            with zipfile.ZipFile(source) as archive:
                data = archive.read(filename)
            assert hashlib.sha1(data).hexdigest() == r.get('sha1')
            files[r.get('name')] = data
        pending[name] = files
    for name, files in pending.items():
        path = BASE/'roms'/f'{name}.zip'
        assert not path.exists()
        with zipfile.ZipFile(path, 'x', zipfile.ZIP_DEFLATED) as archive:
            for filename, data in files.items():
                archive.writestr(filename, data)
        print(f'ROM local preparada: {name}', flush=True)
    return machines


def create_bases(machines):
    for name in sorted(machines):
        bits = name[5:]
        source_rom = {'00':'1943h00111', '01':'1943h01000',
                      '10':'1943h10111', '11':'1943h11000'}[bits[:2]]
        native_folder = ROOT/'bases_nativas'/name
        if (native_folder/'aviao_inicial.sta').exists():
            metadata = json.loads((native_folder/'alvo.json').read_text())
            original = native_folder/'aviao_inicial.sta'
            target, reference = metadata['target'], metadata['reference']
        elif bits[0] == '1':
            model = 'M005' if bits[1] == '0' else 'M006'
            folder = BASE/'captures'/'matriz_colisoes_01'/source_rom
            row = next(r for r in csv.DictReader((folder/'preparacao.csv').open()) if r['modelo'] == model)
            original = folder/f'{model}.sta'
            target, reference = int(row['endereco'], 16), int(row['referencia_1C'], 16)
        else:
            folder = ROOT/'bases_nativas'/source_rom
            metadata = json.loads((folder/'alvo.json').read_text())
            original = folder/'aviao_inicial.sta'
            target, reference = metadata['target'], metadata['reference']
        # Save conversion is restricted to byte-identical program and sound ROMs.
        with zipfile.ZipFile(BASE/'roms'/f'{name}.zip') as a, zipfile.ZipFile(BASE/'roms'/f'{source_rom}.zip') as b:
            for filename in ('01.12d','02.13d','03.14d','05.4k'):
                assert a.read(filename) == b.read(filename), (name, filename)
        data = original.read_bytes()
        assert data[:8] == b'MAMESAVE'
        # Each driver's name participates in MAME's save-registry signature.
        # Require a native save for every set instead of editing the header.
        assert data[10:28].rstrip(b'\0').decode() == name, (name, 'save nativo necessario')
        dest = ROOT/'bases'/name
        dest.mkdir(parents=True, exist_ok=True)
        (dest/'aviao_inicial.sta').write_bytes(data)
        (dest/'alvo.json').write_text(json.dumps(dict(rom=name, source_rom=source_rom,
                     source_save=str(original), target=target, reference=reference,
                     engine=int(bits[1]), language=int(bits[0]), hp=1), indent=2), encoding='utf-8')
    launchers = ROOT/'roms_hibridas'
    launchers.mkdir(exist_ok=True)
    for name in sorted(machines):
        (launchers/f'{name}.cmd').write_text('@echo off\ncd /d "%~dp0..\\..\\.."\n'
             f'python capture_scripts\\laboratorio_inimigo.py {name} --abrir\n'
             'if errorlevel 1 pause\n', encoding='ascii')
    print('32 saves compatíveis e 32 lançadores preparados.', flush=True)


if __name__ == '__main__':
    import sys
    machines = build_missing_roms()
    if '--roms' not in sys.argv:
        create_bases(machines)
