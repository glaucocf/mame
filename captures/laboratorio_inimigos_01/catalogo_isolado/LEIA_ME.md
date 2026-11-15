# Catálogo de testes individuais

Foram executados 87 perfis atingíveis por engine, total 174. Os ensaios preservaram o HP salvo, mantiveram apenas o alvo e suas peças gráficas, o jogador e os projéteis identificados como emitidos pelo alvo. D806 permaneceu em 40. Outros nascimentos foram bloqueados. Partes de chefes foram testadas sem o BG do navio ou Ayako.

Abra `index.html` para consultar as imagens e filtrar os modelos. Cada pasta `<ROM>/<modelo>/` contém `ABRIR.cmd`, que abre aquele perfil no laboratório, com os mesmos comandos da primeira cena. Os IDs M/N são locais a cada engine: o mesmo número não garante o mesmo inimigo.

Nos ensaios de combate, o avião ficou protegido, foi observado o alvo com posição fixa, foram liberados 60 quadros de movimento nativo e o save foi restaurado. Em seguida, foram disparados pulsos de três quadros pressionado/três solto com o laser clássico ou o laser supremo Kai. Não foram alterados HP, força, flags de vulnerabilidade ou leituras de posição das caixas. A fixação atua na posição do alvo; as rotinas de animação, vulnerabilidade e colisão continuam executando. Nos perfis compostos, foram conservadas quatro ou dezesseis peças, conforme a rotina comprovada.

173 perfis chegaram a HP zero por impacto nativo. Kai N003 (construtor fixo 7B6C, referência 5B6A) manteve HP 2 e desapareceu 104 quadros após restaurar esse save, mesmo com posição fixa. Não foi chamado de imune: a matriz anterior confirma que recebe as armas. Nesta cena, a janela e a trajetória não produziram impacto antes da retirada. Fixar coordenadas não congela o tempo de vida.

Os controladores que não apresentaram colisão no estado da matriz e os quatro perfis de projéteis hostis por engine não integram estes 174 alvos. Objetos invisíveis com rotina de alvo foram mantidos no catálogo e identificados como controles ou sem associação visual. Uma peça com gráfico não é automaticamente um inimigo independente.

`CATALOGO_ISOLADO.csv` reúne HP, movimento, peças e contagens. `quadros.csv` registra a posição e o HP a cada quadro; `eventos.csv` conserva os impactos e PCs da rotina. As imagens são capturas do MAME; os arquivos `_sprites.bin` guardam a tabela gráfica correspondente. O relatório anterior de armas continua em `captures/matriz_colisoes_01/`.

O movimento observado pode incluir deslocamento causado pela rolagem; não equivale, por si só, a IA de voo. A quantidade de tiros corresponde a esta janela, não à cadência máxima universal. Os demais objetos são suprimidos, portanto ações dependentes de outro controlador, chefe completo ou fase podem precisar desse contexto em um ensaio posterior. A verificação das cenas manuais testa abertura, HP original, BG desligados e ausência de outros inimigos; a campanha completa não foi refeita aqui.
