# Primeiro inimigo isolado

Pedido autorizado: escolher um inimigo, manter BG desligados e preparar um teste individual. Escolha: avião pequeno da formação inicial, M005 na engine clássica e M006 no Kai, HP original 1.

Usar os saves de nascimento já validados, preservando o contexto de execução e o registro completo. Lua mantém jogador, tiros do jogador, alvo selecionado e, quando identificados pelo emissor, seus projéteis. Bloquear escritas de criação nos demais registros, em vez de apenas ocultar seus gráficos. Recriar o alvo usa sua cópia inicial; não é um criador universal de inimigos.

Começar com posição fixada acima do jogador. Disponibilizar recriação e movimento livre separadamente. Posição fixada não significa IA congelada. Não alterar HP nem aproximar virtualmente as caixas de colisão. Proteção do jogador alternável, energia protegida contra esgotamento.

Controle D806: oito combinações 00/10/20/30/40/50/60/70 nas 36 XMLs; 10=UPPER, 20=LOWER, 40=sprites. O endereço é registrador de escrita, não RAM legível. Desligar o cheat escreve 70 e devolve o controle ao jogo. Caracteres são controlados separadamente por C804.

- [x] Conferir os controles nas 36 XMLs, preservando conteúdo existente.
- [x] Preparar sessão Lua e lançadores locais.
- [x] Executar nas duas engines: pelo menos 300 quadros, nenhuma outra aparição, BG desligados, movimento, recriação e impacto com trajetória natural.
- [x] Conferir imagens do MAME e registrar instruções.
- [x] Abrir a sessão interativa clássica para o usuário.

Ampliação solicitada durante a execução: testar individualmente os demais inimigos/canhões e replicar o lançador para as 32 híbridas.

- [x] Preparar os 28 ZIPs ausentes usando somente os dados locais e conferir CRC/SHA-1 do executável; preservar os quatro existentes.
- [x] Criar um save nativo por variante. Decisão: o nome do driver participa da assinatura do save; copiar apenas o cabeçalho entre variantes não é válido.
- [x] Validar as 32 cenas com 720 quadros cada, HP original, BG desligados, movimento, recriação e colisão nativa.
- [x] Isolar os 87 perfis atingíveis por engine e executar observação/movimento/combate. 173 destruídos; Kai N003 transitório expira antes do impacto. Manter a limitação explícita.
- [x] Gerar 174 lançadores individuais e galeria com os resultados.
- [x] Conferir a abertura das 174 cenas manuais com o controlador final: 45 quadros por cena, HP esperado, nenhuma outra ativação e D806=40.

Limite: componentes de chefes e famílias dependentes de outros controladores ficam para etapas posteriores. Sem commit/push nesta etapa.
