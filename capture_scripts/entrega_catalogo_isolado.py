from pathlib import Path
from collections import Counter
import csv
import html
import json

BASE=Path(__file__).resolve().parents[1]
ROOT=BASE/'captures'/'laboratorio_inimigos_01'
DEST=ROOT/'catalogo_isolado'
rows=[];cards=[]
for rom in ['1943h10111','1943h11000']:
    jobs={r['id']:r for r in json.loads((DEST/rom/'jobs.json').read_text(encoding='utf-8'))}
    results=list(csv.DictReader((DEST/rom/'resultados.csv').open()))
    assert len(results)==87
    for row in results:
        job=jobs[row['modelo']];folder=DEST/rom/row['modelo']
        assert int(row['hp_original'])==job['hp']
        assert row['camadas']=='40'
        with (folder/'quadros.csv').open()as f:
            frames=list(csv.DictReader(f))
        assert len(frames)>=359
        assert all(r['outros_inimigos']=='0'for r in frames)
        impacts=[r for r in csv.DictReader((folder/'eventos.csv').open())if r['evento']=='impacto_natural']
        assert len(impacts)==int(row['impactos_naturais'])
        for impact in impacts:
            assert int(impact['depois'])<int(impact['antes'])
            assert 0xf380<=int(impact['iy'],16)<0xf5c0
        row=dict(rom=rom,rotulo=job['label'],**row)
        rows.append(row)
        launcher=folder/'ABRIR.cmd'
        launcher.write_text('@echo off\ncd /d "%~dp0..\\..\\..\\..\\.."\n'
             f'python capture_scripts\\laboratorio_inimigo.py {rom} --modelo {job["id"]} --abrir\n'
             'if errorlevel 1 pause\n',encoding='ascii')
        prefix=f'{rom}/{job["id"]}'
        engine='1943'if rom=='1943h10111'else'Kai'
        result='Destruído por tiro real'if row['hp_minimo']=='0'else'Temporário; sem impacto neste ensaio'
        cards.append(f'<article data-text="{html.escape((engine+" "+job["id"]+" "+job["label"]).lower())}">'
             f'<img loading="lazy" src="{prefix}/parado.png" alt="{html.escape(job["label"])}">'
             f'<h2>{engine} · {job["id"]} · HP {job["hp"]}</h2><p>{html.escape(job["label"])}</p>'
             f'<p>{row["pecas_graficas"]} peças gráficas · {row["projeteis_emitidos"]} projéteis observados</p>'
             f'<p>{result}</p><p><a href="{prefix}/ABRIR.cmd">ABRIR.cmd</a> · '
             f'<a href="{prefix}/quadros.csv">Quadros</a> · <a href="{prefix}/eventos.csv">Eventos</a></p></article>')
with (DEST/'CATALOGO_ISOLADO.csv').open('w',encoding='utf-8-sig',newline='')as f:
    w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
counts=Counter(r['resultado']for r in rows)
assert len(rows)==174 and counts['destruido_por_disparo_natural']==173
assert [(r['rom'],r['modelo'])for r in rows if r['resultado']!='destruido_por_disparo_natural']==[('1943h11000','N003')]
summary=dict(perfis=174,destruidos_por_disparo_natural=173,temporarios_sem_impacto=1,
             quadros=sum(int(r['quadros'])for r in rows),ativacoes_bloqueadas=sum(int(r['ativacoes_bloqueadas'])for r in rows),
             projeteis_observados=sum(int(r['projeteis_emitidos'])for r in rows))
(DEST/'VALIDACAO.json').write_text(json.dumps(summary,indent=2),encoding='utf-8')
(DEST/'index.html').write_text('''<!doctype html><html lang="pt-BR"><meta charset="utf-8"><title>Inimigos isolados — 1943 e Kai</title>
<style>body{font:16px system-ui;background:#10151b;color:#e8eff7;margin:24px}a{color:#9acbff}input{padding:12px;width:min(650px,90%);font:inherit}main{display:grid;grid-template-columns:repeat(auto-fill,minmax(260px,1fr));gap:18px;margin-top:24px}article{background:#202a35;padding:16px;border-radius:8px}article img{width:224px;max-width:100%;image-rendering:pixelated;display:block;margin:auto}h2{font-size:18px}p{line-height:1.5}header{max-width:950px}</style>
<header><h1>174 perfis isolados</h1><p>87 por engine. 173 destruídos por disparos de trajetória real. Um objeto temporário do Kai expira antes do impacto neste cenário; sua resistência foi confirmada na matriz anterior.</p>
<p>Os nomes com “Visual” são descrições provisórias. A engine clássica usa arte Kai; a engine Kai usa arte clássica. Um gráfico não determina a função. Perfis não equivalem a espécies de inimigos.</p>
<p>Abra ABRIR.cmd na pasta do modelo para experimentar. R restaura a cena, M libera/fixa posição, N troca a arma, I alterna proteção. Os BG ficam desligados.</p>
<input id="busca" placeholder="Filtrar: canhao, aviao, M018, Kai…" aria-label="Filtrar catálogo"></header><main>'''+''.join(cards)+'''</main><script>document.querySelector('#busca').oninput=e=>{let q=e.target.value.toLowerCase();document.querySelectorAll('article').forEach(a=>a.hidden=!a.dataset.text.includes(q))}</script></html>''',encoding='utf-8')
(DEST/'LEIA_ME.md').write_text('''# Catálogo de testes individuais

Foram executados 87 perfis atingíveis por engine, total 174. Os ensaios preservaram o HP salvo, mantiveram apenas o alvo e suas peças gráficas, o jogador e os projéteis identificados como emitidos pelo alvo. D806 permaneceu em 40. Outros nascimentos foram bloqueados. Partes de chefes foram testadas sem o BG do navio ou Ayako.

Abra `index.html` para consultar as imagens e filtrar os modelos. Cada pasta `<ROM>/<modelo>/` contém `ABRIR.cmd`, que abre aquele perfil no laboratório, com os mesmos comandos da primeira cena. Os IDs M/N são locais a cada engine: o mesmo número não garante o mesmo inimigo.

Nos ensaios de combate, o avião ficou protegido, foi observado o alvo com posição fixa, foram liberados 60 quadros de movimento nativo e o save foi restaurado. Em seguida, foram disparados pulsos de três quadros pressionado/três solto com o laser clássico ou o laser supremo Kai. Não foram alterados HP, força, flags de vulnerabilidade ou leituras de posição das caixas. A fixação atua na posição do alvo; as rotinas de animação, vulnerabilidade e colisão continuam executando. Nos perfis compostos, foram conservadas quatro ou dezesseis peças, conforme a rotina comprovada.

173 perfis chegaram a HP zero por impacto nativo. Kai N003 (construtor fixo 7B6C, referência 5B6A) manteve HP 2 e desapareceu 104 quadros após restaurar esse save, mesmo com posição fixa. Não foi chamado de imune: a matriz anterior confirma que recebe as armas. Nesta cena, a janela e a trajetória não produziram impacto antes da retirada. Fixar coordenadas não congela o tempo de vida.

Os controladores que não apresentaram colisão no estado da matriz e os quatro perfis de projéteis hostis por engine não integram estes 174 alvos. Objetos invisíveis com rotina de alvo foram mantidos no catálogo e identificados como controles ou sem associação visual. Uma peça com gráfico não é automaticamente um inimigo independente.

`CATALOGO_ISOLADO.csv` reúne HP, movimento, peças e contagens. `quadros.csv` registra a posição e o HP a cada quadro; `eventos.csv` conserva os impactos e PCs da rotina. As imagens são capturas do MAME; os arquivos `_sprites.bin` guardam a tabela gráfica correspondente. O relatório anterior de armas continua em `captures/matriz_colisoes_01/`.

O movimento observado pode incluir deslocamento causado pela rolagem; não equivale, por si só, a IA de voo. A quantidade de tiros corresponde a esta janela, não à cadência máxima universal. Os demais objetos são suprimidos, portanto ações dependentes de outro controlador, chefe completo ou fase podem precisar desse contexto em um ensaio posterior. A verificação das cenas manuais testa abertura, HP original, BG desligados e ausência de outros inimigos; a campanha completa não foi refeita aqui.
''',encoding='utf-8')
print(json.dumps(summary,ensure_ascii=False),flush=True)
