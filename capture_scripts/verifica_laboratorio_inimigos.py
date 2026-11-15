"""Checks the actual XML definitions and the emulator's isolated-enemy runs."""
from pathlib import Path
import argparse
import csv
import json
import xml.etree.ElementTree as ET

BASE = Path(__file__).resolve().parents[1]
TITLE = 'VIDEO - camadas BG e sprites (D806)'
VALUES = list(range(0, 0x80, 0x10))


def check_xml():
    files = sorted((BASE / 'cheat').glob('1943*.xml'))
    assert len(files) == 36, len(files)
    for path in files:
        found = [c for c in ET.parse(path).getroot().findall('cheat')
                 if c.get('desc') == TITLE]
        assert len(found) == 1, f'{path.name}: falta controle unico de camadas'
        c = found[0]
        assert [int(i.get('value'), 0) for i in c.findall('parameter/item')] == VALUES
        assert c.findtext("script[@state='run']/action") == 'maincpu.pb@D806=param'
        assert c.findtext("script[@state='off']/action") == 'maincpu.pb@D806=70'
    print(f'OK: {len(files)} XMLs, oito combinacoes em cada uma.')


def check_run(path):
    status = json.loads((path / 'validacao.json').read_text(encoding='utf-8'))
    assert status['resultado'] == 'ok', status
    rows = list(csv.DictReader((path / 'quadros.csv').open(encoding='utf-8')))
    assert len(rows) >= 300
    assert all(int(r['outros_inimigos']) == 0 for r in rows), 'outro inimigo escapou'
    assert all(int(r['camadas'], 16) == 0x40 for r in rows), 'BG ativado'
    assert status['criacao_bloqueada'] > 0, 'o bloqueio nao foi exercitado'
    assert status['hp_inicial'] == 1
    assert status['colisao_confirmada'], 'nenhum impacto natural confirmado'
    assert status['movimento_confirmado'], 'movimento nao foi exercitado'
    assert status['reposicao_confirmada'], 'reposicao nao foi exercitada'
    with (path / 'eventos.csv').open(encoding='utf-8') as f:
        events = list(csv.DictReader(f))
    impacts = [r for r in events if r['evento'] == 'hp_reduzido']
    assert len(impacts) == 1
    assert impacts[0]['antes'] == '1' and impacts[0]['depois'] == '0'
    expected_pc = {'00':'5960','01':'5A84','10':'56D1','11':'57DD'}[status['rom'][5:7]]
    assert impacts[0]['pc'] == expected_pc, impacts[0]
    assert int(impacts[0]['iy'], 16) in range(0xF380, 0xF5C0, 0x20)
    print(f'OK: {status["rom"]}, {len(rows)} quadros, alvo unico, BG desligados, '
          'movimento, reposicao e impacto natural.')


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--xml', action='store_true')
    parser.add_argument('--run', type=Path)
    args = parser.parse_args()
    if args.xml:
        check_xml()
    if args.run:
        check_run(args.run)
