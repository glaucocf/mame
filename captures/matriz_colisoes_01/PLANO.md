# Matriz de colisões — execução autorizada

Objetivo: testar as armas válidas em cada engine contra os perfis de inimigos, projéteis e possíveis destroços observados nas duas campanhas em inglês. Testar separadamente contato com o jogador sem invencibilidade. A identidade funcional será atribuída por execução e rotina, além da aparência.

1. [x] Conferir a força por componente de cada arma e observar reduções reais após acertos.
2. [x] Preparar saves reproduzíveis dos perfis do catálogo, preservando a criação e os campos nativos. Excluir jogador, introdução anterior ao controle e encerramento; registrar explicitamente os excluídos.
3. [x] Validar o ensaio em avião pequeno, projétil, canhão, avião grande e possível destroço Kai. Pilotos completos: 20 casos clássicos e 25 Kai; 13 resultados de referência conferidos.
4. [x] Executar cada arma e contato do jogador para os perfis preparados. Aproximar virtualmente as coordenadas durante o teste de colisão, sem alterar flags, resistência ou força para forçar o resultado.
5. [x] Classificar acerto, consumo do tiro, força restante, anulação de projétil, dano ao jogador e ausência de teste conclusivo. Um encontro sem execução do teste não será chamado de imunidade.
6. [x] Repetir os casos com interferência durante a preparação, conferir as flags ativas e entregar tabelas com evidência e limitações. Estados sem colisão ativa ou sem jogador controlável permanecem identificados como tal, sem alegação de imunidade universal.

Arquivos: `auditoria_<ROM>.json` (templates e campos iniciais), `preparacao_<ROM>.csv` (saves de alvos), diretórios por engine para estados e imagens; posteriormente resultados e eventos de cada ensaio. Os registros originais e os GIFs permanecem preservados.

As aproximações usadas no ensaio espacial serão registradas. Testes de geometria, velocidade e alcance natural são distintos do teste de efeito de uma colisão. As duas ROMs mantêm os gráficos cruzados do projeto.

No ensaio isolado, as leituras das flags de colisão de objetos não selecionados são neutralizadas nos pontos conhecidos da rotina. O alvo mantém suas flags nativas. O botão e os projéteis anteriores são limpos imediatamente após a restauração, antes da execução da CPU; isso evita carregar um disparo do caso anterior. A força e a resistência são registradas na própria escrita do impacto, antes que outro acerto ou o fim da trajetória altere os valores.

Etapa adicional necessária: após a matriz inicial, destruir os alvos e observar a criação de novos perfis, pois as passagens sem tiro não revelam todos os destroços e efeitos de morte.

Etapa adicional concluída: 345 destruições observadas em janelas de 120 e 600 quadros. Foram encontrados 16 perfis adicionais, dos quais 15 são objetos de combate/controle incluídos na matriz e um é item/bonus. Os novos alvos atingíveis foram destruídos novamente sem descobrir novas famílias nesse ciclo. Total final: 2.336 ensaios de impacto/contato em 222 perfis, incluindo 336 ensaios exclusivos do componente 09F dos lasers Kai. Os efeitos sem flags ativas não foram chamados de inimigos imunes.
