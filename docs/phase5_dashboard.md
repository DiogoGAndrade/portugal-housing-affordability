# Fase 5 — dashboard interativo

`site/index.html` (≈0,64 MB): página única, **sem dependências externas** (HTML + JS + SVG embebidos), gerada por `python -m housing_pt.dashboard` a partir dos painéis processados, do manifesto INE e do CAOP 2025 simplificado.

## Funcionalidades
- Nível: 308 municípios ou 26 NUTS III (valores NUTS III são medianas publicadas pelo INE, não recalculadas a partir dos municípios).
- Indicadores: I1, I2, I3, I4, I6 (preço e renda), preço nominal e real (euros de 2025), renda, rendimento.
- Ano 2019–2025 (rendimento só até 2024), área de referência 40–120 m² (afeta I2 e I3; muda níveis, não ordenação).
- Escala de cor fixa entre anos (percentis 2–98), divergente centrada em 0 para I6; cinzento = sem dado (não imputado).
- Painel de detalhe com a série da área selecionada; exportação CSV da vista atual; atribuições e lista de fontes (código, data de atualização, data de acesso).
- Painel «Como ler estes números» com as limitações da auditoria; aviso específico em I3 (não comparável a limiares 30 %/40 %) e I4/I6.

## Decisões de desenho
- **Sem ranking nem índice composto**; sem tabelas ordenadas por «pior/melhor».
- **Cenário de prestação (I5) não incluído**: depende de séries BPstat cuja licença não foi verificada.
- Métricas calculadas no navegador com as mesmas fórmulas de `metrics.py`.

## Verificação (2026-11-22)
- Somas e contagens municipais de 2024 de I1, I2 (80 m²), I3, I4, I6 (preço e renda) e preço real calculadas no navegador **coincidem exatamente** com o painel Parquet (ex.: I2: 299 municípios, soma 1870,6459).
- Série de Lisboa mostrada na página coincide com os valores do painel (preço 4 340 €/m², rendimento 16 500 €, I2 = 21,0 em 2024).
- Sem erros na consola; renderização verificada no painel do navegador integrado (município e NUTS III). Layout móvel verificado por emulação (375×812), não em dispositivos reais; sem teste com leitores de ecrã; o contraste/modo escuro seguem `prefers-color-scheme` mas não foram auditados.
- Teste automático `tests/test_dashboard.py`: 308/26 unidades, dados embebidos iguais ao painel, sem carregamentos externos.

## Revisão pós-auditoria (2026-11-22)
Ver `docs/audit_consolidation.md` §4: seletor de área por teclado, mensagens de cobertura, CSV RFC 4180, rótulos prudentes para I3/I4 e rendimento, layout móvel, contraste de controlos, períodos de referência nas fontes. O núcleo de lógica pura (`CORE` no modelo HTML) é testado em Node contra as fórmulas Python.

## Stage 6 (apresentação)
Introdução no topo (pergunta, como usar, três ressalvas), agrupamento dos indicadores em «observados», «derivados» e «derivados com área de referência (pressuposto)» com selo visível junto ao título do mapa, e testes que impedem que um indicador dependente da área seja apresentado como observado.

## Limitações
- Sem pesquisa por texto e sem navegação por teclado polígono a polígono; o seletor «Área selecionada» é a alternativa por teclado.
- Geometria simplificada (tolerância ≈0,002°): adequada a visualização, não a medições.
- Publicação: ver `docs/deployment.md` (Cloudflare Pages, manual; a CI não publica).
