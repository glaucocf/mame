"""Add the layer register selector without rewriting existing cheat definitions."""
from pathlib import Path
from verifica_laboratorio_inimigos import TITLE, check_xml

base = Path(__file__).resolve().parents[1]
labels = {
    0x00: 'UPPER OFF / LOWER OFF / SPRITES OFF',
    0x10: 'UPPER ON / LOWER OFF / SPRITES OFF',
    0x20: 'UPPER OFF / LOWER ON / SPRITES OFF',
    0x30: 'UPPER ON / LOWER ON / SPRITES OFF',
    0x40: 'UPPER OFF / LOWER OFF / SPRITES ON - somente sprites',
    0x50: 'UPPER ON / LOWER OFF / SPRITES ON',
    0x60: 'UPPER OFF / LOWER ON / SPRITES ON',
    0x70: 'UPPER ON / LOWER ON / SPRITES ON - todas ligadas',
}
lines = [f'  <cheat desc="{TITLE}">',
         '    <comment>Registrador de escrita D806: bit 10 UPPER, bit 20 LOWER, bit 40 sprites (hexadecimal). Nao altera caracteres, controlados separadamente por C804. Ao desligar escreve 70 e o jogo retoma o controle das camadas. Nao restaura por leitura: D806 nao e RAM legivel.</comment>',
         '    <parameter>']
lines += [f'      <item value="0x{v:02X}">0x{v:02X} - {label}</item>'
          for v, label in labels.items()]
lines += ['    </parameter>', '    <script state="run">',
          '      <action>maincpu.pb@D806=param</action>', '    </script>',
          '    <script state="off">', '      <action>maincpu.pb@D806=70</action>',
          '    </script>', '  </cheat>', '']
for path in sorted((base / 'cheat').glob('1943*.xml')):
    original = path.read_bytes()
    if TITLE.encode() in original:
        continue
    newline = b'\r\n' if b'\r\n' in original else b'\n'
    block = newline.join(line.encode('utf-8') for line in lines) + newline
    marker = b'  <cheat desc="Test Program Menu (Service Mode)">'
    assert original.count(marker) == 1, path
    updated = original.replace(marker, block + marker, 1)
    assert updated.replace(block, b'', 1) == original, path
    path.write_bytes(updated)
check_xml()
