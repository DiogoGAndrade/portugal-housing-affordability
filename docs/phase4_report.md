# Fase 4 — análise exploratória (preliminar)

Gerado a 2026-11-22. Dados INE (CC BY 4.0), BPstat (licença **não verificada**), CAOP 2025 (DGT, CC BY 4.0). Resultados completos: [`reports/phase4_results.md`](../reports/phase4_results.md). Reproduzir: `python -m housing_pt.phase4`. Semente fixa (`20261122`).

**Aviso geral:** as medianas municipais não têm erro amostral publicado e os municípios não são amostras independentes; os valores-p são **indicativos**. Nada aqui é causal nem diz respeito a uma família concreta.

## 1. Sensibilidade das definições (I2, 2024, 80 m²)

| Variante | Municípios | ρ de Spearman vs. base | Rácio mediano | Mudam de quintil |
|---|---|---|---|---|
| Rendimento bruto por agregado fiscal | 299 | 1,000 | 0,96 | 2 % |
| Rendimento líquido de IRS por sujeito passivo | 299 | 0,998 | 1,22 | 6 % |
| Só alojamentos novos | 152 | 0,927 | 1,16 | 38 % |
| Só alojamentos existentes | 297 | 0,991 | 0,97 | 13 % |

- A ordenação municipal é **robusta** à escolha do rendimento; o rendimento bruto e o líquido de IRS por agregado têm ordenação praticamente idêntica.
- É **sensível** à categoria do alojamento: com apenas «novos», só 152 municípios têm dado e 38 % mudam de quintil. A categoria «Total» é uma mistura que depende da composição local.
- A área de referência (60/80/100 m²) multiplica I2 por uma constante: altera níveis, **nunca** a ordenação.

## 2. Diferenças entre regiões (NUTS II)

Kruskal–Wallis sobre municípios (2024): I2 H = 123,8 (n = 299, 9 grupos), ε² = 0,42; I6 de preço H = 77,7 (n = 283), ε² = 0,28; p < 10⁻¹⁰ em ambos. Uma parte substancial da variação entre municípios está associada à região NUTS II (efeito grande para I2, moderado para I6). Não implica independência entre municípios.

## 3. Autocorrelação espacial (Portugal continental, contiguidade Queen, 999 permutações)

| Variável | n | I de Moran | p simulado | LISA significativos (5 %) |
|---|---|---|---|---|
| ln I2 (2024) | 273 | **0,77** | 0,001 | 55 HH, 61 LL, 3 HL |
| I6 de preço 2019→2024 | 259 | **0,42** | 0,001 | 40 HH, 28 LL, 5 LH, 5 HL |

Forte agrupamento espacial dos níveis de I2 e agrupamento moderado da variação de preço relativamente ao rendimento. Os municípios sem dado foram excluídos (não imputados); as ilhas não entram (sem contiguidade). Esta estrutura é, em parte, mecânica: preços e rendimentos são medianas sobre mercados contíguos.

## 4. Clustering (k-means; ln preço, ln rendimento, I6 de preço; 2024)

| k | silhouette | estabilidade (ARI, subamostras 80 %) |
|---|---|---|
| 2 | **0,36** | 0,97 |
| 3 | 0,29 | 0,76 |
| 4 | 0,27 | 0,84 |
| 5 | 0,28 | 0,83 |
| 6 | 0,30 | 0,79 |

Só **k = 2** é estável e razoavelmente separado. O grupo 0 (152 municípios; preço mediano ≈1 400 €/m², I6 de preço mediano ≈0,28) inclui todos os municípios com dado do Algarve (15), Grande Lisboa (9) e Península de Setúbal (9) e 25 dos 34 do Oeste e Vale do Tejo, mas **também** 57 de Norte e Centro (31 + 26). O grupo 1 (131 municípios; preço mediano ≈606 €/m², I6 de preço mediano ≈0,02) é sobretudo Norte (47), Centro (46) e Alentejo (22). **Tipologias mais finas (k ≥ 3) não são suportadas** por estes três indicadores: silhouette < 0,30 e estabilidade inferior. Conclusão: a estrutura é essencialmente um gradiente de nível de preços; não se propõe tipologia com mais classes nem uma leitura «litoral vs. interior» que a composição por NUTS II não sustenta por inteiro. Perfis em `reports/phase4_cluster_profiles.csv`.

## 5. Quem não tem renda publicada (2024)

244 de 308 municípios têm renda. Os 64 sem renda têm preço mediano claramente mais baixo (≈509 vs. ≈1 043 €/m²; Mann–Whitney p ≈ 10⁻¹³) e rendimento mediano mais baixo (≈13 189 vs. ≈14 224 €; p ≈ 5×10⁻⁸) (medianas de medianas municipais, sem ponderação). Cobertura de renda por NUTS II: Grande Lisboa e Península de Setúbal 100 %, Oeste e Vale do Tejo 97 %, Algarve 94 %, Centro 84 %, Norte 78 %, Alentejo 68 %, Madeira 55 %, Açores 42 %. **A ausência não é aleatória**: está associada a municípios com preços e rendimentos mais baixos; a dimensão do mercado de arrendamento **não foi medida** (não há população nem número de contratos municipais ingeridos), logo não se afirma que sejam «mercados pequenos». Decisão: manter a análise de rendas a nível NUTS III como principal; qualquer resultado municipal de renda deve vir assinalado como subconjunto não aleatório.

## 6. Cenário de prestação (I5) — excluído da publicação

O cenário (prestação mensal de um empréstimo para uma área de referência ÷ rendimento mensal mediano) usava uma série de taxas de juro do BPstat. **Não foram encontrados termos de reutilização do BPstat**, pelo que nenhum resultado derivado dessa série consta deste relatório, do dashboard ou do README. As funções (`monthly_payment`, `payment_to_income`) mantêm-se testadas como aritmética; a análise com dados BPstat só corre localmente com `python -m housing_pt.phase4 --with-bpstat` e escreve para `reports/local/` (ignorado pelo Git). Qualquer uso futuro exige confirmar a licença e a definição da série (nominal ou tipo TAEG, periodicidade) e continua a ser um cenário, nunca elegibilidade de crédito.

## Limitações novas

- «Novos» e «existentes» têm amostras diferentes; usar «Total» como base mantém cobertura, mas mistura composição.
- O I de Moran não separa preços locais de composição do mercado (segundas habitações, turismo, compradores não residentes — risco 10 da auditoria).
- O clustering usa só três variáveis; não inclui renda nem população (população por município não foi ingerida: a API exige dimensões adicionais; fica em aberto).

## Em aberto

Confirmação INE (base do rendimento; revisão das rendas), população municipal, licença BPstat, mudança de regime (séries demasiado curtas — adiada), e a decisão sobre o produto interativo (Fase 5).
