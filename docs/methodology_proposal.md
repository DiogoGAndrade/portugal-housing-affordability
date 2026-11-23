# Proposta metodológica (não implementada)

Estado: **proposta**. Nenhuma fórmula foi calculada com dados reais nesta fase. Notação: município *m*, ano *t*.

- *P*(m,t): preço mediano de venda, €/m² (`0012234`, valor 12 m em T4, categoria Total)
- *R*(m,t): renda mediana de novos contratos, €/m² por mês (`0014698`)
- *Y*(m,t): mediana do rendimento bruto declarado deduzido de IRS por agregado fiscal, €/ano (`0012741`)
- *A*: área de referência do alojamento, m² (pressuposto explícito)

## Indicadores propostos (poucos e complementares; sem índice composto)

| # | Indicador | Fórmula | Pressupostos | Leitura |
|---|---|---|---|---|
| I1 | **m² por ano de rendimento** (compra) | `Y / P` | Nenhum sobre a área | Quantos m² «compra» um ano de rendimento mediano ao preço mediano local. Maior = mais acessível |
| I2 | **Anos de rendimento para um alojamento de referência** | `A·P / Y` com A ∈ {60, 80, 100}; principal A = 80 | A é pressuposto, não observado; sensibilidade obrigatória. Alternativa: área média do município (Censos 2021) se confirmada | Price-to-income para uma casa de referência |
| I3 | **Peso da renda no rendimento** | `12·A·R / Y` | Mesmo A de I2; rendimento por agregado fiscal | Taxa de esforço de entrada no mercado de arrendamento; não é a renda dos inquilinos existentes |
| I4 | **Arrendar vs. comprar** | `12·R / P` (rendimento bruto de renda, razão de medianas) | Medianas de amostras com composição diferente; só indicativo | Relação relativa de custos; não é yield de investimento |
| I5 | **Cenário de prestação** | PMT(taxa BdP, prazo, `LTV·A·P`) / (`Y`/12) | LTV, prazo e taxa documentados e variados (p. ex. LTV 80 %, 30–40 anos); taxa BPstat a identificar | **Cenário de esforço**, não elegibilidade de crédito (DSTI, avaliação bancária, entrada, rendimentos individuais ficam fora) |
| I6 | **Divergência preço–rendimento** | `ln(P_t/P_2019) − ln(Y_t/Y_2019)` (e análogo para R) | Base 2019 (compra) / 2020 (renda); valores nominais; versão real com IPC | Quem ficou mais/menos acessível desde a base |

Valores **nominais e reais** reportados separadamente; deflator IPC/IHPC (código a confirmar; IHPC existe no Eurostat mas só nacional).

## Regras de desenho

1. Um indicador por definição; sem agregação entre definições incompatíveis (preço vs. rendimento com unidades de observação diferentes só combinados através de I1–I6, com limitações escritas).
2. Cada indicador acompanhado de cobertura (n.º de municípios válidos) e de sensibilidade (A, rendimento bruto vs. após IRS, preço novo/existente).
3. Rendimento de base: `0012741`. Sensibilidades: `0012712` (bruto), `0012757` (por sujeito passivo), `0012656` (média de ganhos; base geográfica não confirmada — rotulada).
4. Municípios sem valor aparecem como ausentes, nunca imputados no primeiro marco.
5. Resultados descritos como «mediana local»; não se infere acessibilidade individual.

## Análises científicas avaliadas (viabilidade)

| Análise | Viabilidade | Condições |
|---|---|---|
| Padrões espaciais (Moran's I, LISA) sobre I1/I2 | **Viável** | 304 municípios em 2024; vizinhança por contiguidade CAOP; ilhas tratadas à parte |
| Clustering geográfico | **Viável com cautela** | Variáveis: nível 2024 de I1/I3 e variação I6; justificar k; validar estabilidade; interpretar como tipologia descritiva, não causal; risco R10 de composição |
| Mudança de regime / tendência | **Limitada** | Séries curtas (6–7 anos anuais; 27 trimestres sobrepostos); só nacional/NUTS II/III e com valor 12 m **não sobreposto** (T4); sem inferência forte |
| Divergência preço–rendimento | **Viável** | I6, com decomposição e bandas de sensibilidade |
| Sensibilidade a definições | **Viável e central** | Grelha A × tipo de rendimento × categoria de alojamento |
| Comparações estatísticas entre regiões | **Descritivas/robustez** | Não há IC amostrais; usar testes sobre distribuição de municípios (p. ex. Kruskal–Wallis por NUTS II) com a ressalva de que municípios não são amostras independentes |
| Modelação preditiva / ML | **Não recomendada** | Sem pergunta de investigação que a exija |

## Limitações que têm de constar em qualquer output

Rendimento declarado após IRS ≠ rendimento disponível; agregado fiscal ≠ agregado doméstico; €/m² mediano ≠ preço da casa típica; renda de novos contratos ≠ renda paga; supressão de dados nos municípios pequenos; janelas móveis sobrepostas; segundas habitações/turismo/compradores não residentes influenciam preços e rendas locais.
