# Fase 3 — resultados descritivos (preliminares)

Gerado a 2026-11-22 a partir de dados INE (CC BY 4.0) e CAOP 2025 (DGT, CC BY 4.0). **Descritivo apenas**: sem inferência, sem índice composto, sem ranking formal. Tabelas: [`reports/nuts3_summary.csv`](../reports/nuts3_summary.csv). Figuras: `reports/figures/`. Reproduzir: `python -m housing_pt.build` e `python -m housing_pt.analysis`.

## Métricas implementadas (nominais, salvo indicação)

| Métrica | Definição | Notas |
|---|---|---|
| I1 | rendimento / preço por m² | m² por ano de rendimento; sem pressuposto de área |
| I2 | 80·P / Y (também 60 e 100 m²) | anos de rendimento para um alojamento de referência |
| I3 | 12·80·R / Y (também 60 e 100) | quota do rendimento para arrendar 80 m² a uma renda de **novo contrato** |
| I4 | 12·R / P | razão de medianas, indicativa |
| I6 | ln(x_t/x_base) − ln(Y_t/Y_base), valores reais (IPC 2025=100) | base 2019 (preço) e 2020 (renda). Como preço e rendimento usam o mesmo deflator, o IPC cancela-se em I6; serve para as versões reais dos níveis |

Deflator: IPC anual, Portugal, `0014642`, base 2025 (INE, atualizado 2026-02-11).

## O que os dados mostram (NUTS III, 26 regiões; leitura descritiva)

- **Níveis 2024 de I2 (80 m²)**: de ≈3,3 anos (Alto Alentejo, Beiras e Serra da Estrela, Beira Baixa) a ≈16,7 (Algarve); Madeira 12,9; Península de Setúbal 10,9; Grande Lisboa 15,0; Área Metropolitana do Porto 10,4.
- **Variação 2020→2024 de I2**: aumentos grandes em Alentejo Litoral (8,2→11,1), Algarve (13,6→16,7), Grande Lisboa (11,8→15,0), Madeira (8,9→12,9); descidas em Douro, Viseu Dão Lafões, Beira Baixa e Beiras e Serra da Estrela (preço cresceu menos do que o rendimento).
- **Divergência real preço vs. rendimento 2019→2024 (I6)**: positiva em quase todo o litoral e sul (Península de Setúbal ≈0,45; Madeira ≈0,43; Alentejo Litoral ≈0,39; Grande Lisboa e Área Metropolitana do Porto ≈0,34), negativa em parte do interior Norte/Centro (Beira Baixa ≈−0,22; Douro ≈−0,18). Interpretação: nestas regiões o preço mediano por m² cresceu menos do que o rendimento mediano por agregado fiscal.
- **Renda vs. rendimento (2020→2024)**: I6 de renda positivo em 24 de 26 regiões (próximo de zero em Terras de Trás-os-Montes, 0,01); negativo em Alto Tâmega e Barroso (−0,03) e Açores (−0,04).
- **Municípios** (mapas): maiores valores de I2 concentrados em Lisboa e arredores, litoral algarvio e alentejano; as cores no interior refletem medianas de poucas transações e flutuam mais.

Não são conclusões causais; não se afirma que uma região seja «inacessível» para uma família concreta.

## Limitações e avisos (obrigatórios em qualquer uso destes números)

1. **I3 é um proxy relativo, não uma taxa de esforço convencional, e não é comparável a limiares de 30 %/40 %.** O rendimento mediano é por *agregado fiscal* (definição IRS do INE), não por agregado doméstico, e não é rendimento disponível; 80 m² é uma área de referência, não a habitação de um agregado típico. Valores como 0,81 (Grande Lisboa, 2024) mostram o custo anual de arrendar 80 m² à renda mediana de novos contratos face a esse rendimento, **não** a proporção paga por famílias reais. Usar I3 só em comparações relativas (entre regiões/anos) e com sensibilidade 60/80/100 m².
2. Rendimento = rendimento bruto declarado (definição INE) menos IRS liquidado, por agregado fiscal (não disponível). Base geográfica **não confirmada** (ver `docs/audit_consolidation.md`).
3. Preço = mediana 12 meses a T4; renda = mediana de novos contratos (metodologia 2026, ainda sujeita à confirmação do texto INE).
4. Municípios sem dados ficam cinzentos (preço: 305/308 em 2025; rendimento 2024: 299/308; I6 de preço: 283/308) — não imputados.
5. Medianas municipais pequenas têm ruído amostral desconhecido (INE não publica IC): os extremos dos mapas I6 em pequenos concelhos do interior devem ser lidos com cautela.
6. Segundas habitações, turismo e compradores não residentes afetam preços e rendas locais; não controlados.
7. I4 compara medianas de amostras com composição diferente (compra vs. novos contratos).

## Estado

Implementado: I1–I4, I6, versões reais, tabela NUTS III, 2 mapas municipais. Por fazer (Fase 4): autocorrelação espacial, clustering justificado, sensibilidades A×rendimento×categoria, comparação NUTS II com testes não paramétricos, cenário de prestação (BPstat), perfil das lacunas de renda.
