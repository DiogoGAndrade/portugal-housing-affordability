# Relatórios gerados

Ficheiros produzidos pelo pipeline (`python -m housing_pt.build`, `analysis`, `phase4`, `findings`). Não são dados brutos; são tabelas, texto e figuras derivadas.

**Atribuição (obrigatória):** os valores de preço, renda, rendimento e IPC são do «Instituto Nacional de Estatística – Portugal (Statistics Portugal)», licença CC BY 4.0, **sem modificação**; os indicadores I1–I6, as variações e os valores reais (deflacionados) são **cálculos do autor**. As geometrias das figuras usam «Informação geográfica cedida pela Direção-Geral do Território» (CAOP 2025, CC BY 4.0), simplificadas. Códigos dos indicadores, períodos de referência e datas de atualização: `data/manifests/ine_manifest.json` e [`DATA_LICENCES.md`](../DATA_LICENCES.md).

| Ficheiro | Conteúdo |
|---|---|
| `coverage_report.md` | cobertura por ano e variável (municípios e NUTS III) e proveniência |
| `linkage_report.md` | testes de comparabilidade entre séries antigas e atuais |
| `nuts3_summary.csv` | valores NUTS III oficiais (preço, renda, rendimento) e métricas derivadas |
| `phase4_results.md`, `phase4_metrics.json`, `phase4_sensitivity.csv`, `phase4_cluster_profiles.csv` | análise exploratória (observacional, sem inferência causal) |
| `findings.md` | texto dos principais resultados, gerado por `python -m housing_pt.findings` |
| `figures/` | mapas estáticos |
