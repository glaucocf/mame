# Referência nativa dos aviões para a frente gráfica SEGA

`captura_movimentos_jogadores.py` executa o MAME com o script Lua de mesmo
nome. Captura os dois jogadores em `1943h10000` (1943) e `1943h11111` (Kai),
sem pular quadros, isolando os aviões sobre fundo preto.

```powershell
python capture_scripts\captura_movimentos_jogadores.py 1943h10000
python capture_scripts\captura_movimentos_jogadores.py 1943h10000 --cold
python capture_scripts\captura_movimentos_jogadores.py 1943h11111
python capture_scripts\captura_movimentos_jogadores.py 1943h11111 --cold
```

Execute a partir de `mame-src`, com `1943h.exe`, as ROMs e as bases do
laboratório de inimigos disponíveis. Os arquivos estão em
`captures/movimentos_jogadores_01/<rom>/`; `cold/` inclui a decolagem desde
o início real do jogo. `status.txt` registra a conclusão.

- `dma.bin`: registros de 4.101 bytes: quadro uint32 little-endian,
  byte de controle C804 e os 4.096 bytes de F000–FFFF no pedido de DMA.
- `quadros.csv`: direção, tempo, estados, posições e paletas de ambos.
- `mame_*.png`: amostras visuais do movimento; não substituem os registros.
- `dois_jogadores.sta`: estado com ambos ativos.

O contador volta a zero quando começa a passagem controlada de movimento.
Os registros anteriores no modo cold preservam a sequência de decolagem.
O ator principal 1P começa em F200 e o 2P em F280; cada avião usa o par
de registros principal e principal+20. Os demais registros incluem auxiliares.

O port independente está em
[SEGADEV/1943hybrid/graficos](https://github.com/glaucocf/81632itdoes-segadev/tree/main/1943hybrid/graficos).
Seu extrator usa as ROMs originais, as PROMs e estes registros para gerar
tiles, paletas e a sequência observada; os pixels não são redesenhados.
As ROMs gráficas preservam os tocadores de áudio existentes em SEGADEV.
