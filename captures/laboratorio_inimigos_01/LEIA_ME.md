# Avião pequeno isolado

Abra `ABRIR_1943.cmd` ou `ABRIR_KAI.cmd`. O primeiro usa engine 1943 com arte Kai; o segundo, engine Kai com arte 1943. Ambos começam com um avião da formação inicial, HP original 1, acima do jogador. Não há UPPER nem LOWER. Os caracteres do jogo ficam ocultos; a identificação e os comandos são apresentados por cima da janela.

Para as outras combinações, abra a pasta **roms_hibridas** e dê dois cliques no CMD com o nome desejado, por exemplo `1943h00000.cmd`. Há um lançador para cada uma das 32 ROMs. Todos começam com a mesma família de avião; cada ROM usa sua própria programação, gráficos e paleta. Cada variante tem um save criado nativamente nela, sem converter o cabeçalho de outro jogo. `verificacao_32_roms.json` reúne os 32 ensaios de abertura, isolamento, movimento, recriação e impacto real.

Os 28 ZIPs que faltavam em `mame-src/roms` foram montados com os dados locais já existentes, conferidos pelos CRCs e SHA-1 esperados pelo executável. Os quatro ZIPs já presentes foram preservados. Não foram alterados bytes de programa. As cópias de apoio dos conjuntos originais ficam em `roms_suporte/`, evitando depender de arquivos antigos do OneDrive que não estavam disponíveis localmente.

Para escolher outros inimigos, abra **catalogo_isolado/index.html**. Cada pasta `<ROM>/<modelo>/` contém seu próprio **ABRIR.cmd**, inclusive para os canhões. São 87 perfis por engine nas duas ROMs inglesas catalogadas. Os 32 lançadores da pasta `roms_hibridas` são da cena inicial; os demais modelos ainda não foram catalogados nas programações japonesas.

| Controle | Ação |
| --- | --- |
| Setas | Mover o jogador |
| Ctrl esquerdo | Disparar |
| R | Restaurar a cena inicial, incluindo alvo, jogador e energia |
| M | Alternar entre posição fixa e movimento nativo do alvo |
| N | Selecionar a próxima arma; o valor aparece na tela |
| I | Ligar/desligar a proteção do jogador |
| T | Permitir/bloquear projéteis emitidos pelo próprio alvo |
| P | Pausar/continuar pelo MAME |
| Esc | Encerrar |

Fixar a posição mantém a animação e a lógica do inimigo. Não é congelamento de IA. O alvo pode ser destruído; use R para repetir. O movimento livre também pode fazê-lo sair da tela. A energia do jogador é reabastecida quando baixa; I desliga a invulnerabilidade para observar colisões. Não recupera automaticamente um jogador já morto: R restaura a cena.

O isolamento bloqueia as escritas de ativação de outros objetos e mantém seus registros inativos e fora da tela. Conserva o jogador e seus tiros. A admissão de tiros do inimigo exige o emissor selecionado e o construtor nativo identificado. Nenhum tiro do avião inicial foi observado nos dois ensaios de 720 quadros; o comando T não é demonstração de que esse perfil dispara em qualquer contexto.

Nos ensaios automáticos, o alvo permaneceu sozinho, foi liberado para voar, foi recriado e recebeu um disparo normal seguindo a trajetória real. O HP caiu de 1 para 0 pela rotina do jogo, sem aproximação virtual das caixas nem alteração da resistência. `verificacao/` preserva imagens, quadros, eventos e resultados por ROM. `sessao/` registra a execução manual; os arquivos dessa pasta são renovados ao abrir outra sessão da mesma ROM.

## Seletor de camadas nas XMLs

As 36 XMLs `cheat/1943*.xml` possuem **VIDEO - camadas BG e sprites (D806)**:

| Valor hexadecimal | UPPER | LOWER | Sprites |
| --- | --- | --- | --- |
| 00 | OFF | OFF | OFF |
| 10 | ON | OFF | OFF |
| 20 | OFF | ON | OFF |
| 30 | ON | ON | OFF |
| 40 | OFF | OFF | ON |
| 50 | ON | OFF | ON |
| 60 | OFF | ON | ON |
| 70 | ON | ON | ON |

Ao desligar o cheat, escreve 70 e o jogo retoma o controle. D806 é um registrador de escrita: não se recupera o estado anterior lendo esse endereço. Os caracteres usam o controle separado C804 e não são alterados por esse cheat.

A sessão isolada usa Lua e mantém D806=40 continuamente. O menu de cheats não é carregado pelos lançadores desta sessão. O seletor XML destina-se também às execuções normais do MAME com cheats habilitados.

## Catálogo individual

Os ensaios dos 174 perfis atingíveis ficam em `catalogo_isolado/`, separados por engine e modelo. 173 foram destruídos por tiros de trajetória real. Um objeto temporário do Kai desaparece antes do impacto neste cenário; não foi chamado de imune. O relatório explica a limitação e remete à matriz anterior, que confirma sua resistência. Partes de chefes foram testadas sem reconstruir navios ou Ayakoes em BG.
