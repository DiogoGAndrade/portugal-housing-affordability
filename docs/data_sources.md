# Inventário de fontes de dados

Acedido em **2026-11-22**. Legenda de verificação: **V** = verificado diretamente (API/metadados lidos nesta sessão); **C** = apenas catálogo dados.gov.pt / pesquisa (código existe, não sondado); **N** = não verificado.

Acesso INE (V): `https://www.ine.pt/ine/json_indicador/pindica.jsp?op=2&varcd=<COD>&Dim1=T&lang=EN` (dados) e `.../pindicaMeta.jsp?varcd=<COD>&lang=EN` (metadados). Sem chave. Limites: ≤1 000 000 linhas/pedido; ≤15–20 pedidos/s. Geocódigos: 1–2 car. = país/NUTS I–II, 3 = NUTS III, 7 = município (308), 9 = freguesia.

## A. Compra

| Variável | Código INE | Descrição / unidade | Geografia | Cobertura | Cobertura municipal observada | Notas | Verif. |
|---|---|---|---|---|---|---|---|
| Preço mediano de venda, últimos 12 meses (Metod. 2022) | **0012234** | €/m² × categoria (Existente/Nova/Total), NUTS 2024 | país→freguesia | Trim., 2019T4–2026T2; atualizado 2026-10-23 | Total: 286/308 (2019T4) → 304/308 (2026T2) | Janela móvel de 12 meses → observações sobrepostas | V |
| idem, por tipologia | 0012241 | × Tipologia do fogo | NUTS 2024 | Trim. | n/d | | C |
| Preço mediano anual (Metod. 2022) | 0012254 (tipologia), 0012255 (categoria) | €/m², anual | NUTS 2024 | Anual | n/d | Candidato a valor anual não sobreposto | C |
| Preço mediano do trimestre | 0012239, 0012240 (× domicílio fiscal / setor do comprador) | €/m² | NUTS 2024 | Trim. | n/d | Não é a série principal | C |
| Série legada (Metod. 2018) | **0009490** | €/m², 12 meses, NUTS 2013 | até município | Trim., 2016T1–2021T3 | 302–306/308 | Sobreposição 2019T4–2021T3 com 0012234 permite teste de ligação | V |
| Nº de transações | **0012785** | N.º, × categoria, domicílio e setor comprador, NUTS 2024 | **sem linhas municipais** (apenas códigos de 1–2 car.) | Trim., 2009T1–2026T2 | 0 | Impede ponderação/limiar de amostra municipal por esta série | V |
| Valor das transações (€) | 0012786 (trim.), 0012788 (anual) | € | NUTS 2024 | | n/d | | C |
| Índice de preços da habitação (nacional/UE) | Eurostat `prc_hpi_q` | Índice 2015=100 / 2025=100; TOTAL/DW_NEW/DW_EXST | **só país** | 2005T1–2026T2 | — | Útil para contexto nacional | V |

## B. Arrendamento

| Variável | Código INE | Descrição | Geografia | Cobertura | Cobertura municipal observada | Notas | Verif. |
|---|---|---|---|---|---|---|---|
| Renda mediana de novos contratos (**Metod. 2026**) | **0014698** | €/m², anual, NUTS 2024 | até freguesia | 2020–2025; atualizado 2026-09-29 | 222/308 (2020) → 247/308 (2025) | Série revista; ver risco R-RENT | V |
| idem, com geografia 2025 | 0014773 | | NUTS 2024 / geografia 2025 | Anual | n/d | | C |
| idem, 12 meses | 0014696 (NUTS 2024) / 0014771 | | | Trim./Semestral | n/d | | C |
| idem, só locatários residentes em Portugal | 0014700 | | | 12 meses | n/d | Útil para sensibilidade | C |
| idem, municípios >100 000 hab. | 0014706, 0014704, 0014702 | | 24 municípios aprox. (nome do indicador) | Trim. | n/d | | C |
| Série anterior (Metod. 2021), NUTS 2024 | 0012600 | €/m², anual | até freguesia | até 2024 (V); atualizado 2025-06-27 | n/d | Descontinuada na prática pela Metod. 2026 | V (metadados) |
| Série anterior, NUTS 2013 | 0009631 | | | 2017–2023 | 199–215/308 | | V |
| Nº de novos contratos | — | **Não encontrado** como indicador municipal | — | — | — | Reportado em comunicados INE a nível agregado | N |
| Rendas do stock de contratos (existentes) | — | **Não investigado** (Censos 2021 / Inquérito às Condições de Vida e Rendimento) | | | | Necessário para distinguir mercado vs. stock | N |

## C. Rendimento

| Variável | Código INE | Descrição | Geografia | Cobertura | Cobertura municipal | Notas | Verif. |
|---|---|---|---|---|---|---|---|
| **Mediana** do rend. bruto declarado deduzido de IRS **por agregado fiscal** | **0012741** | € | NUTS 2024, 308 municípios + 3 092 linhas de freguesia | Anual 2018–2024; atualizado 2026-07-24 | 297–299/308 | Exclui agregados com valor <0 (nota INE). Residência fiscal do declarante. | V |
| idem, NUTS 2013 | 0009953 | € | NUTS 2013 | 2015–2021 | 297–298/308 | Sobreposição 2018–2021 | V |
| Mediana do rend. bruto declarado por agregado fiscal | 0012712 | € | NUTS 2024 | Anual | n/d | Variante bruta (sensibilidade) | C |
| Mediana por sujeito passivo (deduzido de IRS) | 0012757 | € | NUTS 2024 | Anual | n/d | Unidade de observação diferente | C |
| Média por agregado fiscal (deduzido de IRS) | 0012740 | € | NUTS 2024 | Anual | n/d | Média sensível a outliers | C |
| Distribuição por quintis | 0012743 | € | NUTS 2024 | Anual | n/d | Permite análise por quintil | C |
| Gini | 0012744, 0012760 | % | NUTS 2024 | Anual | n/d | | C |
| Ganho médio mensal (Quadros de Pessoal) | **0012656** | € (média), NUTS 2024 | Município | Anual 2021–2024 | 308/308 | **Média**, trabalhadores por conta de outrem; ver R1/R2 | V |
| Rendimento disponível das famílias NUTS II | Eurostat `tgs00026` / `nama_10r_2hhinc` | M PPS / € | NUTS 2 | 2013–2024 | — | Base de residência não verificada nesta sessão; só NUTS II | V |

## D. Contexto económico

| Variável | Fonte / código | Estado |
|---|---|---|
| IHPC | Eurostat `prc_hicp_midx` | Existência V; último período **N** |
| IPC (deflator nacional) | INE | **N** — código a identificar |
| Taxas de juro de novos empréstimos à habitação | Banco de Portugal BPstat, API `https://bpstat.bportugal.pt/data/v1/` | API V (200 em `/domains/`); série concreta e licença **N** |
| Encargos com habitação / sobrecarga | Eurostat `ilc_lvho07a` | Existência V; nível geográfico **N** |
| Construção / licenciamento, alojamentos, agregados, população | INE (Censos 2021, Estimativas) | **N** — códigos a identificar no Stage 1 |
| Área média dos alojamentos por município | INE (Censos 2021) | **N** — crítico para converter €/m² em preço de casa típica |

## E. Geografia

| Recurso | Fonte | Estado |
|---|---|---|
| CAOP 2025 (GeoPackage) | DGT. Continente `https://geo2.dgterritorio.gov.pt/caop/CAOP_Continente_2025-gpkg.zip`; Açores `.../CAOP_RAA_2025-gpkg.zip`; Madeira `.../CAOP_RAM_2025-gpkg.zip` | URLs lidos na página DGT (V); ficheiros **não descarregados**; licença **não declarada** na página |
| Relação freguesia/município/NUTS | `https://www.dgterritorio.gov.pt/sites/default/files/ficheiros-cartografia/Areas_Freg_Mun_Dist_Pais_CAOP2025.zip` | V (URL) |
| Alterações CAOP 2025 | `.../alteracoes_CAOP2025.pdf` | V (URL) |
| Modelo de dados | `https://github.com/dgterritorio/CAOP` | Referenciado, **não lido** |
| Códigos | 308 municípios em todas as séries sondadas (2016–2026); versões NUTS: 2013, 2024, «2024 – geografia 2025» | V |

## F. Fontes agregadoras

- **PORDATA** republica dados INE/Eurostat; termos de utilização sem licença aberta nem API/bulk encontrados → usar INE diretamente. (V, ver auditoria)
