# Material de pesquisa versionado

Este diretório conserva os avanços da análise de 1943/1943 Kai e do laboratório de testes para o port SEGA.

- `laboratorio_inimigos_01/`: lançadores das 32 híbridas, saves nativos, controlador de inimigos, 174 cenas individuais e evidências de validação. Abra seu `LEIA_ME.md` para os comandos e `catalogo_isolado/index.html` para escolher um perfil.
- `matriz_colisoes_01/`: matriz de 2.336 ensaios, catálogo funcional, saves por perfil, eventos e imagens. A conferência posterior dos três segmentos do laser clássico fica em `1943h10111_laser_tres_segmentos/`.
- `gifs_armas_01/`: GIFs individuais e comparativos, registros de sprites e análise de força por componente.
- `<ROM>/catalogacao_01/analise/`: catálogos das campanhas, séries gráficas e folhas de referência.
- `<ROM>/gatinho_teste_01/`: reprodução controlada da coleta do gatinho da sorte.
- Os relatórios deste nível conservam os índices das campanhas e a análise do gatinho e dos testes de serviço.

Os scripts Python e Lua ficam em `capture_scripts/`. O controlador usa o executável `1943h.exe` deste projeto e os ZIPs locais em `roms/`. O repositório não inclui ROMs, executável, configurações pessoais ou as centenas de milhares de imagens e registros brutos das campanhas; esses arquivos continuam no workspace original. Os resultados selecionados, os saves de teste e os scripts de captura foram preservados aqui. Os saves exigem uma compilação compatível do MAME: a assinatura depende do driver e da estrutura do estado.

Para verificar a entrega no ambiente com executável e ROMs disponíveis:

```
python capture_scripts/verifica_entrega_laboratorio.py
python capture_scripts/verifica_32_laboratorios.py
python capture_scripts/verifica_inicios_catalogo.py
```

Os primeiros verificadores conferem as oito combinações de camadas em 36 XMLs e os resultados das cenas. As duas últimas execuções repetem os ensaios das 32 variantes e a abertura dos 174 perfis, respectivamente. Os comandos recriam seus arquivos de execução. As sessões manuais ficam em diretórios `sessao/`, ignorados pelo Git.

Alguns relatórios históricos registram caminhos absolutos da máquina de captura. O lançador resolve os saves do catálogo também a partir da pasta `captures/` do checkout atual. Os arquivos `jobs.lua` são entradas geradas pelos scripts e podem ser regenerados no ambiente de destino.

O catálogo registra 174 perfis, que incluem componentes e objetos auxiliares; não são 174 espécies de inimigos. 173 chegaram a HP zero por disparo natural. O objeto temporário Kai N003 expirou antes do impacto na cena isolada; isso não demonstra imunidade. As limitações de contexto e de classificação visual estão nos relatórios específicos.
