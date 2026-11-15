# Rastreamento das campanhas

Cada execução escreve em `captures/<ROM>/campanha/<execução>/`.

- `fNNNNNNN.png`: imagem nativa 224 × 256 do quadro indicado, a cada quatro quadros e na mudança do ID da fase.
- `eventos.csv`: quadro, evento, bytes E450 e E451, energia atual F206, capacidade E12F, rolagens UPPER e LOWER e valor do evento. Os IDs das fases começam em zero. O evento `protecao_energia` informa uma intervenção na energia atual, lida antes da escrita de proteção.
- `ram.zlib`: stream zlib. Cada registro descomprimido tem 10.251 bytes: quadro uint32 little endian, bytes D000–D806 (2.055 bytes) e bytes E000–FFFF (8.192 bytes). Todos os quadros emulados são registrados, antes da aplicação dos cheats pelo script. Inclui RAM de caracteres, atributos, registradores de rolagem, estado do jogo e RAM de sprites. A ativação de camadas D806 é um registrador somente de escrita, portanto sua leitura no bloco não substitui o rastreamento das escritas.
- `fase_XX_fNNNNNNN.sta`: estado salvo ao mudar o ID E450. Um estado em fase 00 no início pode preceder a entrada da partida.
- `continuar.sta`: estado no encerramento do trecho.

Invencibilidade usa F214=02. A proteção de energia escreve 32 em F206 quando o valor lido está entre 1 e 11. A capacidade E12F é controlada pelo jogo. No modo com tiro, o script escolhe Three Way, tempo infinito de arma e rapid fire. O CSV registra a interferência na energia para permitir interpretar a recarga.

O emulador executa sem espera de tempo real, com frameskip=0. A numeração dos quadros começa em cada execução. As versões japonesas com engine Kai foram excluídas a pedido do usuário.

## Execuções e limites da campanha

`campanha_com_tiro_01` é a campanha capturada nas três ROMs 1943h10111, 1943h00111 e 1943h11000. As três chegaram à cena final e aos créditos. Os retornos ao início após os créditos foram observados nos quadros 161530, 166731 e 290271, respectivamente. Os quadros posteriores incluem a demonstração automática do jogo. O índice `captures/campanhas_fases.csv` usa somente a primeira passagem de cada ID e termina a fase 16 nesse retorno.

No Kai inglês, a primeira mudança de ID ocorreu em 10093 e a segunda em 149380. Esse intervalo contém a rolagem longa na primeira transição e o combate da segunda fase. A transição foi aguardada durante a execução.

`observacao_02`, somente em 1943h10111, contém 18000 quadros sem disparos, atravessando a primeira fase e parte da segunda. `observacao_01` foi uma tentativa de inicialização que falhou na gravação da compressão. Seu arquivo de memória não é utilizável e essa tentativa fica excluída do índice.

Os comandos de som são escritas no latch C800. A coluna de comandos 20–34 no índice é um inventário por intervalo, sem atribuir automaticamente uma faixa a uma subcena. A identificação de um comando como música de combate, resultado ou transição requer sua posição no CSV. Estas execuções registram comandos de som e não geram um novo arquivo de áudio.

A correspondência individual entre canhões e corpos de chefes, a extração textual dos scores e destruction rates e a análise das músicas por cena são trabalhos de análise posteriores. O material de referência para fazê-los está capturado.
