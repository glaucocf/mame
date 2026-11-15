# Catálogo das duas campanhas em inglês

As duas execuções passaram pelas 16 fases, exibiram o encerramento e voltaram após os créditos. A memória foi registrada em todos os quadros; imagens a cada quatro quadros, mais mudanças de fase. Não foi usado frameskip.

| ROM | Quadros consecutivos de RAM | Imagens PNG | Perfis de criação por LDIR |
| --- | ---: | ---: | ---: |
| 1943h10111 | 224,577 | 56,159 | 110 |
| 1943h11000 | 352,755 | 88,200 | 111 |


## Organização

Em `captures/<ROM>/catalogacao_01/` ficam as imagens `f0000004.png`, `f0000008.png` etc., os saves por fase, checkpoints a cada 600 quadros e os dados brutos. Os nomes possuem zeros à esquerda para ordenar corretamente.

Dentro de `analise/`, `avioes_canhoes.csv` reúne a triagem dessas famílias, e `modelos.csv` conserva todos os perfis, incluindo projéteis, efeitos, jogador e registros sem associação visual. Cada linha contém template de origem, banco, PC após a cópia, referência +1C, registro de exemplo, fases e imagem de referência. `modelos_01.png` e seguintes mostram as peças gráficas observadas. `fases.csv` indica os intervalos; `validacao.json` contém a conferência da captura.

## O que está identificado

O [laboratório de inimigos isolados](laboratorio_inimigos_01/LEIA_ME.md) permite abrir a cena inicial nas 32 híbridas e consultar 174 perfis individuais das duas engines inglesas. O [catálogo visual](laboratorio_inimigos_01/catalogo_isolado/index.html) reúne imagens, HP e lançadores para testar cada perfil sem BG.

A verificação funcional posterior está em [Matriz controlada de colisões](matriz_colisoes_01/LEIA_ME.md), com 2.336 ensaios em 222 perfis e 345 destruições observadas. Consulte esse relatório para função de colisão, força restante e dano ao jogador; os rótulos abaixo continuam descrevendo a triagem gráfica inicial.

Correção de interpretação: nestas combinações cruzadas, 1943h10111 usa engine 1943 com sprites Kai, e 1943h11000 usa engine Kai com sprites 1943. Conforme informado pelo autor do projeto, posições gráficas que mostram aviões no 1943 podem representar destroços de navios no Kai, cuja programação intensifica as explosões. Assim, uma peça desenhada como avião não comprova a criação de um avião inimigo. Os CSVs agora separam engine, conjunto de sprites, função na engine e evidência da função. Os rótulos baseados apenas no desenho recebem o prefixo Visual. A categoria continua sendo uma triagem gráfica.

O autor esclareceu também que os destroços de chefes no Kai causam dano ao avião. São objetos perigosos com colisão, e devem ser distinguidos de inimigos e de efeitos visuais sem dano. A criação após a destruição do chefe é uma pista para identificá-los; o dano não pode ser avaliado apenas pela sobrevivência do jogador nas capturas com invencibilidade. Ainda não foram atribuídos perfis específicos a essa função.

As primeiras formações pequenas, formações vermelhas, peças de aviões maiores, embarcações e várias séries de canhões já têm gráficos e origens associados. Os rótulos descritivos do catálogo são uma triagem visual por série gráfica, não nomes militares nem um identificador universal de inimigo. Há perfis ainda a confirmar.

Um mesmo avião grande ou canhão pode usar vários registros. Um mesmo gráfico pode ser usado por comportamentos diferentes. Portanto, os 110/111 perfis não significam 110/111 espécies de inimigos. A associação de peças filhas ao controlador e a reprodução individual de cada comportamento ainda não estão completas. Os bancos são independentes em cada engine. Banco -1 significa ROM fixa.

A coluna `fases` usa número humano (RAM E450 + 1); o valor 17 nessa coluna indica o encerramento, não uma fase adicional. O índice `fases.csv` já o apresenta como FINAL.

## Condições da execução

Invencibilidade em F214 e proteção contra esgotamento de energia. Nenhum tiro até observar 17.000 quadros da fase final. A partir daí foi selecionada uma vez a arma 04 e mantido tiro para destruir a YAMATO. As intervenções constam dos eventos e da validação. Não foi necessária a varredura lateral prevista como recurso final.

A destruição da YAMATO foi capturada nos dois engines. A destruição dos chefes anteriores não foi provocada nesta rodada; seus efeitos de destruição ainda não têm cobertura completa nesta nova captura.

A longa rolagem inicial do Kai foi aguardada. Não houve correção de ROM. Ambas as campanhas alcançaram as 16 fases e o encerramento.

`objetos.csv` registra candidatos a nascimento por transição de +08 de zero para não zero. Essa condição é confirmada como ocupação no pool dos pequenos; em outras famílias permanece candidata. A tabela de modelos inclui apenas cópias LDIR reconhecidas, não pretende cobrir qualquer possível criação por escritas individuais. `graficos.csv` relaciona alterações gráficas com quem as escreveu. `dma.zlib` conserva todas as posições de sprites a cada transferência real ao vídeo; `ram.zlib`, a RAM quadro a quadro.

## Gatinho

O objeto e a coleta foram reproduzidos separadamente nos dois engines: 10 no clássico e 50 no Kai, sem escrever diretamente na arma. Não apareceu naturalmente nestas duas novas passagens. Ao revisar as capturas antigas com tiro, foram encontrados registros do gatinho nas demonstrações após os créditos. Consulte [GATINHO_DA_SORTE.md](GATINHO_DA_SORTE.md) para os intervalos, templates, testes e condições já descobertas.
