from pathlib import Path
import csv
base=Path(__file__).resolve().parents[1]/'captures'/'matriz_colisoes_01'
checks={
 '1943h10111':{
  'M005_arma_00':('atingiu_e_consumiu_tiro',0,1,0),
  'M005_arma_08':('atingiu_e_continuou',0,1,0),
  'M005_arma_10':('atingiu_e_continuou',0,47,0),
  'M008_arma_02':('atingiu_e_consumiu_tiro',0,1,0),
  'M011_arma_10':('atingiu_e_continuou',0,40,0),
  'M018_arma_10':('atingiu_e_continuou',0,33,0),
  'M005_contato':('causou_dano_ao_jogador',1,0,8)},
 '1943h11000':{
  'M006_arma_03':('atingiu_e_continuou',0,1,0),
  'M009_arma_03':('atingiu_e_continuou',0,1,0),
  'M012_arma_50':('atingiu_e_consumiu_tiro',7,5,0),
  'M019_arma_50':('atingiu_e_consumiu_tiro',10,5,0),
  'M109_arma_50':('atingiu_e_continuou',0,1,0),
  'M109_contato':('causou_dano_ao_jogador',4,0,32)}
}
for rom,expected in checks.items():
    folder=base/(rom+'_ensaios_piloto')
    assert 'estado=concluido' in (folder/'status.txt').read_text()
    rows=list(csv.DictReader((folder/'resultados.csv').open()));byid={r['caso']:r for r in rows}
    assert len(rows)==len(byid)==(20 if rom=='1943h10111' else 25)
    for case,values in expected.items():
        row=byid[case];got=(row['resultado'],int(row['resistencia_final']),int(row['forca_final']),int(row['dano_por_contato']))
        assert got==values,(rom,case,got,values)
    print(rom,len(rows),'casos completos;',len(expected),'resultados de referencia conferidos',flush=True)
