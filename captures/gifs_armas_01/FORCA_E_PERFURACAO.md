# Força restante e passagem através de inimigos

Resultado observado nas ROMs 1943h10111 (engine 1943) e 1943h11000 (engine Kai), usando o save e o protocolo dos GIFs. São unidades internas do campo +0D de cada componente de tiro, não uma medida de dano universal para qualquer alvo.

| Arma | Força inicial no 1943 | Força inicial no Kai |
| --- | ---: | --- |
| 00 Normal | 1 | 1 |
| 01 Auto | 1 | 1 (arma por cheat) |
| 02 Shot Gun | 1 | 2 (arma por cheat) |
| 03 Shot Gun + | 1 | 2 |
| 04 Three Way | 1 | 1 |
| 08 Shell | 2 | 3 |
| 10 Laser | 48 em cada um dos três segmentos (30 hexadecimal) | componentes com 3 e 2 |
| 30 Laser + | não reconhecido | componentes com 4 e 2 |
| 50 Laser supremo | não reconhecido | componentes com 5 e 2 |

No Kai, os valores dos dois componentes do laser não devem ser somados automaticamente como se representassem um único acerto. Eles são registros de projéteis separados e podem colidir em momentos distintos.

Verificação posterior dos três segmentos clássicos: cada um usa o código 096, começa com força 48 e mantém seu próprio campo +0D. Foram feitos 12 impactos isolados (três segmentos contra quatro resistências). Todos apresentaram as mesmas regras. Na captura natural, o quadro 41 mostra forças 47, 48 e 48 nos registros 1C, 1D e 1E, comprovando a redução independente. Veja `captures/matriz_colisoes_01/1943h10111_laser_tres_segmentos/LEIA_ME.md`.

## Confirmação em execução

Os oito casos com força inicial superior a um foram repetidos com um observador das escritas no campo +0D. Todos apresentaram reduções positivas por acerto na rotina de colisão com inimigos: PC após a gravação **56F8** no clássico e **5804** no Kai. Foram exemplos 2→1 no Shell clássico, 48→47 no laser clássico, 2→1 nos dois Shot Guns Kai e 3→2 no Shell Kai. Nos lasers Kai foram observadas reduções nos dois componentes.

Os arquivos `colisoes/registros/<ROM>/<arma>/reducoes_forca.csv` guardam quadro, endereço do tiro, força anterior e posterior, PC, IX (alvo), IY (tiro), tipo do alvo e código gráfico. Não foram observadas nessas linhas as rotinas distintas de interceptação de projéteis inimigos nem uma simples reinicialização por cópia de template.

## Regra encontrada no programa

Para os inimigos tratados por essa rotina, se a energia restante do alvo for menor que a força do tiro, a energia do alvo é zerada e essa quantidade é subtraída da força do tiro. O tiro continua ativo com o restante. Se o alvo tiver energia igual ou maior, o tiro é consumido; o alvo recebe a redução correspondente.

Consequentemente, ter força superior a um permite atravessar certos alvos, mas não garante atravessar qualquer inimigo. Os tiros de força um não deixam sobra positiva contra um alvo dessa rotina com energia positiva. Os resultados não encerram o estudo de inimigos especiais, blindagem, destroços ou colisão entre projéteis.

`forca_tiros_observada.json` conserva a leitura inicial do DMA dos GIFs; ela pode reunir apenas o resultado final de vários acertos ocorridos no mesmo quadro. O registro das escritas acima é a confirmação mais precisa da causa e da sequência das reduções.
