# Auditoria de consolidação

Data: 2026-11-22. Âmbito: consolidar o que existe (Fases 0–5); sem novas fases de investigação.

## 1. Estado recuperado

| Verificação | Resultado |
|---|---|
| Testes de partida | 12 passam localmente |
| Segredos / dados brutos no Git | pesquisa de padrões de segredo: nenhum; ficheiros rastreados em `data/`: só `.gitkeep` e os dois manifestos; sem `.parquet`/`.gpkg`/`.zip` |
| Alterações não relacionadas | nenhuma: o diff contra `main` só toca ficheiros deste projeto; nenhum outro repositório foi acedido |

## 2. Rastreio fonte → valor mostrado

| Indicador no dashboard | Fonte oficial | Transformação | Valor mostrado |
|---|---|---|---|
| Preço (€/m²) | INE `0012234`, categoria «Total», mediana dos últimos 12 meses (metodologia 2022) | valor do 4.º trimestre de cada ano (janela de 12 meses terminada em T4) | igual ao valor INE, sem alteração |
| Renda (€/m²/mês) | INE `0014698` (metodologia 2026), anual | nenhuma | igual |
| Rendimento (€/ano) | INE `0012741`, mediana por agregado fiscal | nenhuma | igual |
| NUTS III | os mesmos indicadores, linhas de 3 caracteres | nenhuma (**valores oficiais, não médias de municípios**) | igual; testado que diferem da média simples dos municípios |
| IPC | INE `0014642`, base 2025=100, «Total», Portugal | usado em preço real | 2025 = 100 verificado no pipeline |
| I1, I2, I3, I4, I6 | fórmulas de `metrics.py` | calculadas no navegador com a mesma fórmula | testado em Node contra Python e contra o painel Parquet |

Cadeia verificada por testes automáticos: `tests/test_dashboard.py` (entradas embebidas = painel para 308 municípios × 7 anos; I2 do dashboard = I2 do pipeline; site comitado = site reconstruído) e `tests/test_dashboard_js.py` (fórmulas JS = fórmulas Python).

## 3. Auditoria metodológica

### A. Definição do rendimento
Fonte mais autoritativa acessível: metadados INE do indicador (`https://www.ine.pt/bddXplorer/htdocs/minfo.jsp?var_cd=0012741&lingua=PT`, lidos no navegador integrado a 2026-11-22) e página INE da publicação «Estatísticas do rendimento ao nível local – Indicadores de rendimento declarado no IRS – 2024» (ISSN 2184-7177).

Confirmado:
- Fonte: dados anonimizados da Autoridade Tributária (nota de liquidação do IRS, Modelo 3). Periodicidade anual, 2018–2024, atualizado em 2026-07-24.
- Unidade de observação: **agregado fiscal** (agregado familiar tal como definido para efeitos de IRS: cônjuges não separados/unidos de facto e dependentes, etc.).
- **Rendimento bruto declarado**: rendimento não isento *antes* das deduções específicas nas categorias A (trabalho dependente) e H (pensões); nas restantes categorias, rendimento *depois* das respetivas deduções específicas. Ou seja, mistura de bruto e líquido de deduções específicas, conforme a categoria.
- **IRS liquidado**: coleta líquida das deduções e benefícios fiscais, antes de retenções na fonte e de pagamentos por conta.
- Nota INE: exclui agregados com valor (rendimento bruto menos IRS) inferior a zero.
- As folhas-resumo da publicação cobrem municípios com 2 000 ou mais sujeitos passivos e as 26 NUTS III; a API devolve valores para ~298 municípios.

**Não confirmado** (nenhuma fonte lida o estabelece): base geográfica (residência fiscal ou outra), tratamento das contribuições para a Segurança Social, proporção de agregados unipessoais/pensionistas. A publicação PDF (45 MB) não foi lida (a ferramenta de leitura falhou e não foi descarregada).

Consequências aplicadas: removida a afirmação «anterior à Segurança Social» e a hipótese «muitos agregados de uma pessoa/pensionistas» (eram inferências); o rótulo passou a «rendimento bruto declarado deduzido do IRS liquidado, por agregado fiscal», com a incerteza sobre base geográfica visível no dashboard e na documentação. Não se afirma que represente residentes, trabalhadores nem rendimento disponível.

### B. Comparabilidade histórica
- **Chave municipal**: `geocod` muda com a versão NUTS; junção feita por `dico` (308/308, único, validado contra INE 2013/2024 e CAOP 2025). Teste: `test_geographic_joins`, `test_dico_is_stable_join_key`.
- **Preço**: série atual (metodologia 2022) desde 2019T4; a série legada (2018) **não** é unida ao nível municipal (20–25 % dos municípios diferem >5 % na sobreposição). **Rendimento**: legado idêntico na sobreposição (possível recuo a 2015, não aplicado no dashboard). Nenhuma união silenciosa.
- **Rendas (metodologia 2026)**: só a série nova (2020–2025). A descrição oficial da revisão **não foi lida** (páginas INE renderizadas no cliente); mantém-se o risco R-RENT e a limitação no dashboard.
- **Lacunas**: nada é imputado nem extrapolado (testado em Node: entradas em falta → `null`, CSV com célula vazia). Cobertura medida e fixada em limites no teste `test_temporal_coverage_bounds`.
- **Datas**: rendimento até 2024; preço até 2025T4 (e 2026T2 na fonte); renda até 2025. O controlo de ano mostra 2019–2025 e, se não há dado, explica porquê.

### C. Fórmulas e unidades (verificadas)
| Métrica | Fórmula | Unidades |
|---|---|---|
| I1 | Y / P | (€/ano) / (€/m²) = m²/ano |
| I2 | A·P / Y | m² · €/m² / (€/ano) = anos |
| I3 | 100·12·A·R / Y | 12·m²·(€/m²/mês) / (€/ano) = adimensional, em % |
| I4 | 100·12·R / P | (€/m²/ano) / (€/m²) = 1/ano, em % ao ano |
| I6 | ln(x_t/x_base) − ln(Y_t/Y_base) | adimensional; IPC cancela-se (mesmo deflator) |
| Preço real | P·100/IPC_t | € de 2025 por m² |

- A área A (60/80/100; 40–120 no dashboard) é sempre apresentada como **pressuposto, não área observada**; não existe qualquer área média observada no projeto.
- **I3** passou a ser rotulado como «proxy renda/rendimento» (não é uma taxa de esforço convencional). **I4** é a razão entre duas medianas de populações diferentes; deixou de ser descrito como arrendar vs. comprar de forma ambígua e o dashboard diz que não é rentabilidade de investimento realizada. Nenhum texto rastreado usa «yield» como resultado.
- CPI: base 2025=100 verificada (`build.py` falha se `CPI[2025] != 100` ou se a série acaba antes de 2024).

### D. Resumos geográficos
- NUTS III/NUTS II no dashboard e nas tabelas da Fase 3: **valores oficiais do INE**; testado que não são médias simples de municípios.
- Resumos **construídos** (rotulados como tal): mediana não ponderada entre municípios (fase 4: I5 por ano, medianas dos municípios com/sem renda; perfis de clusters). Não representam uma estatística regional oficial.

### E. Análise estatística (revisão e correções)
- **NUTS II (Kruskal–Wallis)**: efeito de grupo grande para I2 (ε² 0,42); valores-p indicativos (medianas sem erro amostral; municípios não independentes). Mantido.
- **Moran/LISA**: só continente; forte estrutura espacial é em parte mecânica (medianas de mercados contíguos). Mantido com essa ressalva.
- **Clusters**: **corrigido**. O texto dizia «litoral, áreas metropolitanas e Algarve, sobretudo»; a composição real do grupo de preços altos inclui 57 municípios de Norte/Centro. Reescrito com contagens reais; só k=2 estável; sem tipologia fina.
- **Lacunas de renda**: **corrigido** «mercados pequenos» (a dimensão do mercado não foi medida); passou a «preços e rendimentos mais baixos».
- **Cenário de prestação**: **corrigido** o texto «o aumento das taxas pesa tanto como a subida dos preços» (afirmação sem decomposição). Na sequência da auditoria (Stage 6) os resultados derivados do BPstat foram **retirados dos ficheiros versionados** por falta de termos de reutilização; a análise passou a ser opcional e local (`--with-bpstat`, `reports/local/`, ignorado pelo Git). Continua separado da elegibilidade de crédito.
- Sensibilidades: ranks robustos ao rendimento (ρ ≥ 0,998), sensíveis à categoria «novos» (ρ 0,93; 38 % mudam de quintil). Mantido.

### F. Licenças e atribuição (fontes oficiais)
| Fonte | Licença e obrigação | Verificado em | Cumprimento |
|---|---|---|---|
| INE (dados e API) | CC BY 4.0; citar «Fonte: Instituto Nacional de Estatística – Portugal (Statistics Portugal)», identificar a informação e o período de referência; indicar modificações | `ine_cont_inst&INST=3585857`, `ine_api_v2` | Dashboard: crédito INE, lista de indicadores com **período de referência**, data de atualização e acesso; «valores originais não modificados; métricas calculadas pelo autor» (teste `test_dashboard_carries_required_credits`) |
| DGT CAOP 2025 | CC BY 4.0; mencionar que a DGT é a entidade proprietária; texto «Informação geográfica cedida pela Direção-Geral do Território» ao publicar, mesmo adaptada | página DGT «dados abertos» e registo dados.gov.pt CAOP2025 | Texto presente no dashboard, README, figuras e manifesto; geometria simplificada **indicada** |
| Banco de Portugal BPstat | **Termos de reutilização não encontrados** (páginas devolvem shell JS ou 403; nenhum registo BPstat em dados.gov.pt). A série 12710738 é uma taxa de juro de novos empréstimos, percentil 50, taxa fixa; o BPstat não indica nos metadados lidos se é nominal ou tipo TAEG nem a periodicidade explicitamente | tentativas descritas acima | **Nenhuma série BPstat pode ser considerada redistribuível.** Continua fora do dashboard (teste `test_dashboard_excludes_unlicensed_bpstat_data`). O relatório da Fase 4 mantém o cenário como análise interna, com a ressalva |
| Eurostat | Citado só na documentação (`prc_hpi_q`, `tgs00026`); não usado em dados mostrados | — | n/a |

## 4. Defeitos corrigidos no dashboard (sem redesenho)
1. Mapa só operável com rato → novo seletor «Área selecionada» (teclado e leitores de ecrã), sincronizado com o mapa.
2. Anos sem dados (p.ex. rendimento 2025, renda 2019) deixavam o mapa cinzento sem explicação → mensagem com o que o indicador requer.
3. CSV: delimitador `;` e decimais com ponto (ambíguo no Excel pt-PT) → CSV RFC 4180 (vírgulas, aspas), coluna da área de referência, unidade, fonte; células vazias para valores em falta; lógica testada.
4. Texto sobre rendimento/Segurança Social/mercados pequenos sem suporte → reescrito (ver A e E).
5. Layout móvel: SVG e insets fixos → fluídos; tabela com scroll próprio; sem scroll horizontal da página a 375 px.
6. Contraste de bordas de controlos (1,57:1) → ~4:1 (≥3:1); contraste de texto 6,9–16:1 (claro) e 7,6–15,3:1 (escuro).
7. Etiquetas acessíveis: `label for`, `aria-live` para título/cobertura, `scope` nas tabelas, nomes `aria-label` nos mapas; foco visível.
8. Fontes do dashboard passaram a mostrar o período de referência (exigência do INE).

## 5. Questões abertas (não bloqueiam o merge; documentadas)
- Base geográfica do rendimento e tratamento da Segurança Social (ler `ERendimentoNL2024.pdf` ou pedir ao INE).
- Texto oficial da revisão metodológica das rendas de 2026.
- Licença e definição completa (nominal/TAEG, periodicidade) das séries BPstat.
- Área média por município e população municipal (não ingeridas); análise de mudança de regime adiada.
- Mapa SVG não navegável polígono-a-polígono pelo teclado (o seletor é a alternativa); sem teste com leitores de ecrã reais; o teste móvel foi por emulação do painel (375×812), não em dispositivos.
- Testes que dependem dos painéis locais (`tests/test_dashboard.py`, cobertura temporal) **ficam ignorados na CI** (não há dados no repositório); correm localmente. Não existe configuração de lint no projeto, por isso a CI não corre lint.
