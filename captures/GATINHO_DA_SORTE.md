# Gatinho da sorte: objeto nativo confirmado

Foram feitos testes separados das duas campanhas, carregando o checkpoint do quadro 1800 e copiando o template nativo do gatinho para um registro livre. Não houve escrita em F251 para conceder a arma. No quadro local 80, o item foi aproximado do jogador; a rotina de coleta do próprio jogo concedeu a arma e removeu o item.

| ROM | Template na ROM fixa (32 bytes) | Tipo em +0A | Arma concedida | PC observado após a escrita em F251 |
| --- | --- | --- | --- | --- |
| 1943h10111 | 7270 | 0A | 10 | 58C5 |
| 1943h11000 | 73E1 | 0F | 50 | 59B9 |

Os quatro gráficos da animação são **5C4, 5C5, 5CC e 5CD**, paleta **9**. O atributo gráfico é A9. A identificação visual foi conferida no atlas e nas imagens reais do emulador.

## Onde conferir

- `1943h10111/gatinho_teste_01/f0004.png`: gatinho antes da coleta, olhando para a frente.
- `1943h11000/gatinho_teste_01/f0004.png`: o mesmo teste no engine Kai.
- `gatinho_teste_01/eventos.csv`, em cada ROM: criação, gráficos, coleta e desativação do objeto.
- `gatinho_teste_01/metadados.json`: save inicial e origem do template.
- `1943h11000/catalogacao_01/analise/gatinho_candidato_graficos.png`: quatro quadros ampliados da animação. O nome conserva “candidato” por ter sido gerado antes da confirmação.

## Momento de aparição natural

Nas duas novas campanhas, não houve aparição natural com esses gráficos/paleta nas transferências de sprites, nem coleta de laser. Portanto, não há um quadro natural confirmado nessas execuções. A passagem foi sem tiro até a observação final da YAMATO; isso reduz os bônus dependentes de destruir inimigos.

A revisão dos registros antigos **com tiro** encontrou o gatinho nas **demonstrações após os créditos**, com E450 = 02 (cenário da fase 3). Esses momentos não pertencem à campanha jogada que já havia terminado:

| ROM | Primeiro quadro com o gráfico na RAM | Último quadro | Registro |
| --- | ---: | ---: | --- |
| 1943h10111 | 162583 | 163222 | 34 |
| 1943h10111 | 172804 | 173443 | 34 |
| 1943h10111 | 288642 | 289017 | 34 |
| 1943h11000 | 299049 | 299688 | 3B |

Os arquivos ficam em `captures/<ROM>/campanha/campanha_com_tiro_01/`. No clássico, a imagem **f0163100.png** contém o quadro 5CD/p9 nas coordenadas **(40,160)** da imagem. No Kai, **f0299092.png** contém o quadro 5C4/p9 em **(192,200)**. Ambas as correspondências foram conferidas pixel a pixel com os gráficos da ROM. Algumas outras posições ficam sob o logotipo; as coordenadas mudam durante a demonstração. Os registros, tipos e referências estão em `catalogacao_01/analise/gatinho_campanha_anterior.json`. O primeiro registro na RAM pode preceder a entrada completa na área visível e não é necessariamente o instante da criação.

No engine clássico, a rotina fixa **7254** consulta o valor anterior de **E00E**, soma 99 e grava o resultado. Só continua a criar o gatinho se o nibble baixo do valor anterior for zero. A seleção de bônus em **59FE–5A50** encaminha o marcador **+15 = 08** para essa rotina. Isso foi confirmado pela leitura do programa; não é ainda uma reprodução controlada de toda a sequência de morte do inimigo.

No Kai, há a rotina equivalente em **73B6**, com a mesma condição em E00E e o template **73E1**. A tabela de seleção de bônus difere; não se deve transportar o marcador 08 do clássico sem verificar o caminho correspondente. A cópia direta do template 73E1 foi testada e concedeu 50 corretamente.

## Base comprovada para o futuro XML

1. Procurar um registro livre entre **F5C0 e F7A0**, passo **20 hexadecimal**, verificando **+08 = 00**. São 16 registros do pool compartilhado com aviões pequenos e itens.
2. Copiar os **32 bytes completos** do template da ROM correta para esse registro, uma única vez.
3. Ajustar **+02 = Y** e **+03 = X** nas coordenadas internas do vídeo. A tela final tem rotação; esses eixos não são diretamente os da imagem em retrato.
4. Deixar o jogo animar, movimentar e coletar o item. Não travar a criação a cada quadro: isso recriaria o gatinho após a coleta e poderia sobrescrever outro objeto.

Nos testes, os registros livres escolhidos foram F6A0 no clássico e F680 no Kai. **Esses endereços não são exclusivos do gatinho** e não devem ser fixados como se fossem uma posição reservada.

Nenhum cheat de aparição do gatinho foi acrescentado às XMLs nesta etapa. A receita acima já foi validada em execução para orientar essa próxima edição.
