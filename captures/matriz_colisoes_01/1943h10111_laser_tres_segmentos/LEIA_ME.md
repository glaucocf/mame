# Os três segmentos do laser clássico

ROM 1943h10111, arma 10. Cada segmento foi selecionado separadamente no primeiro disparo após limpar o pool, mantendo a força nativa. Os outros segmentos foram afastados somente durante a leitura espacial do ensaio, para que não atingissem o mesmo alvo.

| Segmento, de cima para baixo | Código gráfico | Força inicial decimal | Campo da força no primeiro disparo |
| --- | --- | ---: | --- |
| Superior | 096 | 48 | F38D |
| Central | 096 | 48 | F3AD |
| Inferior | 096 | 48 | F3CD |

Os endereços acima correspondem à primeira alocação neste teste. São registros reutilizáveis, não posições exclusivas e permanentes do laser. O driver desenha objetos 16×16; os valores desta análise pertencem aos registros lógicos de projétil, não a cada subdivisão gráfica de 8×8.

Foram conferidos os 12 resultados em [resultados.csv](resultados.csv). Para os três segmentos, os resultados foram iguais:

| Energia do alvo | Resultado do alvo | Resultado do segmento |
| ---: | --- | --- |
| 1 | Destruído | Continua com 47 |
| 8 | Destruído | Continua com 40 |
| 15 | Destruído | Continua com 33 |
| 64 | Fica com 16 | Segmento consumido |

A captura natural original também mostra, no quadro local 41, as forças **47, 48, 48** nos registros 1C, 1D, 1E. Portanto, reduzir a força do segmento superior não reduz automaticamente a dos outros dois. Essa evidência está em `captures/gifs_armas_01/independencia_laser_1943.json`, e as posições/códigos em `segmentos_laser.json`.

No Kai, a ordem observada é 096 acima (força 3, 4 ou 5 para armas 10, 30 e 50) e 09F abaixo (força 2 nos três níveis). Também são componentes separados. As forças não são automaticamente somadas como se qualquer contato recebesse todos os segmentos: isso depende de quais registros efetivamente colidem com o alvo.

Estes 12 ensaios são uma verificação posterior à matriz de 2.336 casos; não estão incluídos naquele total.
