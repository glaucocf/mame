# Primeiras identificações das campanhas

## Tanque

A capacidade E12F começa em 64 no quadro 363 das três execuções. Aumenta oito unidades durante as conclusões das fases 3, 6, 9, 12 e 15, atingindo 104. Os instantes exatos estão em `tanque_alteracoes.csv`. A energia atual é F206 e a capacidade E12F. O script de captura protegeu somente F206 próximo do esgotamento.

Nas campanhas com tiro, a proteção agiu quatro vezes em 1943h00111: quadros 20068, 23428, 28114 e 31474. A leitura era 11 e foi elevada a 32. Não houve intervenção nas outras duas campanhas até o retorno após os créditos.

## Laser e entrada secreta

O usuário identificou o gatinho da sorte como item do laser secreto e informou os códigos de arma 0x10 no clássico e 0x50 no Kai. A coleta desse item deve ser conferida visualmente e relacionada à mudança da arma.

Uma experiência adicional partiu do mesmo estado salvo na mudança para a fase 3 de 1943h10111. Sem o cheat que fixa a arma, o controle manteve F251=04. Segurando P1 Cima + Direita + botão 1 + botão 2, F251 mudou para 10 no quadro local 18 e a tela passou a mostrar LASER. O comando de P1 sozinho foi suficiente. Também foi feita uma tentativa com P2 Baixo + botão 2 simultâneo, com o mesmo resultado. Essas imagens e CSVs estão em `1943h10111/analise_codigo_fase03`.

A alteração de arma foi medida, mas a ligação dessa experiência com o mecanismo de aparição/coleta do gatinho ainda exige observar os quadros iniciais. A experiência não incluiu a variante Kai nem estabelece seu comando secreto.

A campanha principal força Three Way a cada quadro. Portanto, sua duração de armas e seus pickups são influenciados pelo cheat. A ausência de laser prolongado nessa execução não permite concluir ausência do gatinho.

Na varredura da RAM das três campanhas, não houve amostra com F251=50. Nas campanhas clássicas também não houve F251=10. No Kai inglês ocorreram cinco amostras transitórias de F251=10: quadros 190217 (fase 7), 200029 e 200665 (fase 8), 209839 (fase 9) e 276717 (fase 16). Esses valores são pontos para investigação e não confirmam coleta do gatinho. O código esperado para o laser secreto do Kai, conforme informação do usuário, é 50.

## Regras das armas esclarecidas pelo dono

Estas informações foram fornecidas pelo dono em 13/11/2026. A lista compartilhada de opções no XML oferece valores além dos reconhecidos normalmente por cada engine. A presença da opção no XML não comprova sua disponibilidade durante a partida.

| Valor F251 | 1943 | Kai |
|---|---|---|
| 00 Normal | Disponível. | Disponível. A eventual diferença do desenho e dos códigos de sprite ainda será conferida. |
| 01 Auto | Disponível normalmente. | Programada, acessível por cheat. |
| 02 Shot Gun | Disponível normalmente. | Programada, acessível por cheat. |
| 03 Shot Gun+ | Obtida ao coletar um segundo item Shot Gun. | Única opção de Shot Gun disponível normalmente. O desenho muda e os endereços de sprites são os mesmos, segundo o dono. |
| 04 Three Way | Disponível. | Disponível. |
| 08 Shell | Disponível. | Disponível. O desenho muda e os endereços de sprites são os mesmos, segundo o dono. |
| 10 Laser | Arma suprema obtida pelo gatinho da sorte. | O mais fraco dos três lasers. |
| 30 Laser+ | Não reconhecido pelo engine. | Evolução ao coletar o item Laser pela segunda vez. |
| 50 Laser++ | Não reconhecido pelo engine. | Arma suprema obtida pelo gatinho da sorte. |

Segundo a descrição estrutural do dono, o laser é a diferença de composição entre os sistemas de armas: no 1943 são três células 8×8 da mesma sprite, empilhadas verticalmente. No Kai são duas células 8×8 empilhadas, com um endereço de sprite para a parte superior e outro para a inferior. Os endereços numéricos e os efeitos dos patches do híbrido devem ser medidos separadamente. O desenho Normal (00) permanece a conferir.

Para o port, preservar a identidade dos códigos e das peças gráficas compartilhadas. A disponibilidade por engine, a progressão por coleta e o gatinho devem seguir a tabela acima. As três opções Laser do XML não devem ser tratadas automaticamente como três armas válidas no engine clássico.
