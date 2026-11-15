# Matriz controlada de colisões — 1943 e Kai

Foram concluídos **2336 ensaios de impacto/contato em 222 perfis** e **345 destruições observadas**. Os perfis incluem inimigos, projéteis, componentes e efeitos; essa contagem não equivale a espécies de inimigos. Os dois conjuntos são 1943h10111 (engine 1943, sprites Kai) e 1943h11000 (engine Kai, sprites 1943).

## Resultados principais

Nos projéteis hostis que usam a rotina própria identificada, Shot Gun 02 e 03 fazem a interceptação. Os demais valores de arma testados não entram no teste espacial dessa rotina. Objetos que usam a rotina comum de alvo são uma categoria diferente: podem receber todas as armas e alguns também causam dano por contato. Não se deve classificar um objeto pela aparência do sprite.

Quando o alvo comum, composto ou grande tem energia menor que a força do componente que o atinge, ele é destruído e o componente continua com a diferença. Quando a energia é igual ou maior, o componente é consumido. Na rotina dos projéteis hostis, o projétil hostil é anulado no encontro aceito, mesmo quando seu campo 0B é maior que a força do tiro; esse campo não deve ser chamado indiscriminadamente de energia.

O componente 09F dos lasers Kai tem força 2 nos três níveis. Foram feitos 336 ensaios próprios desse componente, separadamente da peça 096, cuja força inicial é 3, 4 ou 5. Os códigos 10, 30 e 50 continuam sujeitos à mesma seleção de colisão contra os projéteis hostis, pois não possuem o bit de arma usado pelos Shot Guns.

O perfil Kai M109 (construtor banco 4:8392, referência 5B6A), encontrado na sequência após destruição de canhão, recebeu todas as armas. Tem valor 0B 4 e retirou 32 pontos de energia por contato. O perfil clássico N003 usa o construtor correspondente 4:8392, referência 5A59, e também causou 32. O clássico N004, construtor 4:83B2, causou 8. A designação visual específica desses fragmentos pode ser revisada com as imagens e rotinas.

## Arquivos para consulta

- [CATALOGO_FUNCIONAL.csv](CATALOGO_FUNCIONAL.csv): um registro por perfil, função determinada pela rotina, construtor, referência, armas com acerto e dano por contato.
- [MATRIZ_ARMAS.csv](MATRIZ_ARMAS.csv): 2.000 casos principais, com força, estado do tiro, valor do alvo antes/depois e PC da primeira interação.
- [MATRIZ_LASER_09F.csv](MATRIZ_LASER_09F.csv): 336 casos do segundo componente dos lasers.
- [CONTATO_JOGADOR.csv](CONTATO_JOGADOR.csv): contato com invencibilidade desligada para os 222 perfis.
- [PROJETEIS_HOSTIS.csv](PROJETEIS_HOSTIS.csv): perfis confirmados pela rotina própria de projéteis.
- [OBJETOS_APOS_MORTE.csv](OBJETOS_APOS_MORTE.csv): 16 perfis adicionais observados nas janelas posteriores às mortes; um é item/bonus, fora da matriz de combate. A janela temporal sozinha não prova que cada nascimento foi causado pela morte.
- [DESTRUICOES.csv](DESTRUICOES.csv), [EXCLUIDOS.csv](EXCLUIDOS.csv) e [VALIDACAO.json](VALIDACAO.json): cobertura e conferência.

Os diretórios de ensaios preservam resultados brutos e eventos com endereço, valor anterior/posterior, PC, IX e IY. Os diretórios de destruição preservam nascimentos, banco, construtor, pilha, saves e imagens dos novos perfis.

## Como os ensaios foram isolados

Cada caso restaurou o mesmo save do perfil. Foram limpos os botões e os tiros anteriores antes da CPU voltar a executar. A arma e seu tempo foram selecionados como nos cheats existentes. As coordenadas foram aproximadas durante a leitura da caixa de colisão, respeitando os centros diferentes das rotinas simples, compostas e grandes. As flags, o valor do alvo e a força do componente não foram alterados para forçar um acerto.

Nos pontos conhecidos de decisão de colisão, as interações de objetos não selecionados foram suprimidas. Durante os dois quadros de preparação, o alvo também ficou protegido nessas leituras; suas flags na RAM foram preservadas e voltaram a ser usadas normalmente no ensaio ativo. Foi observado o reaproveitamento do registro, para não atribuir ao alvo original a interação com um objeto substituto. Para contato, a energia começou em 64 e F214 ficou em zero após a preparação. O dano informado usa o valor imediatamente anterior e posterior à escrita feita pela rotina do próprio alvo. A força após impacto vem da escrita dessa colisão, não de um quadro posterior em que o projétil poderia ter saído da tela.

A observação após as mortes usou primeiro 120 e depois 600 quadros, sem frameskip. Os novos objetos atingíveis foram destruídos novamente; nesse segundo ciclo curto não surgiram perfis adicionais desconhecidos. A observação longa encontrou ainda dois controladores tardios de explosão, que receberam sua própria rodada de testes.

## Limites de interpretação

Este é um ensaio do efeito de uma colisão no estado salvo. Não é uma medição de alcance, velocidade ou formato exato da caixa em voo natural. Objetos com flags de colisão inativas, jogador ainda sem controle ou ausência de tiro ativo têm esse resultado explicitamente registrado; não foram chamados de imunes. Os estados futuros de um controlador não são demonstrados por um único save.

O campo 0B pode representar energia, peso/dano de projétil ou um valor de controle, conforme a rotina. Os nomes brutos resistencia_inicial/final foram conservados nos arquivos para rastreabilidade. Cada estado de arma, escudo, jogador 2, dificuldade e ramo secreto adicional pode exigir ensaio próprio. Não foi alterado o programa das ROMs nem acrescentado cheat às XMLs nesta etapa.
