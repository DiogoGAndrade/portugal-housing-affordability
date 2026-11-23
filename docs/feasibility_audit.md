# Auditoria de viabilidade (Stage 0)

Data de acesso: **2026-11-22**. Método: leitura de metadados/amostras via API pública INE e Eurostat, páginas oficiais (INE, DGT, dados.gov.pt, BPstat), e a sonda `scripts/stage0_audit_probe.py` (nenhum dataset descarregado para o repositório). Códigos e contagens no inventário: [`data_sources.md`](data_sources.md).

## 1. Licenças e acessibilidade

| Fonte | Acesso máquina | Licença / reutilização | Estado |
|---|---|---|---|
| INE (API JSON, sem chave) | `pindica.jsp?op=2`, `pindicaMeta.jsp` | CC BY 4.0, citar fonte e período de referência; indicar modificações. Dados da API «de carácter público». ≤1 M linhas/pedido, ~15–20 pedidos/s, HTTP 429 se excedido; não ligar o Power BI diretamente (guardar localmente) | V |
| dados.gov.pt (espelho de metadados INE) | API `api/1/datasets/` | Datasets INE marcados `cc-by` | V |
| Eurostat | API JSON-stat 2.0 `.../api/dissemination/statistics/1.0/data/{code}` | Reutilização autorizada com citação (Decisão 2011/833); texto CC BY 4.0 aplica-se explicitamente ao conteúdo editorial; algumas fontes de terceiros com restrição não comercial | V (rótulo exato dos dados: parcialmente) |
| Banco de Portugal BPstat | API `https://bpstat.bportugal.pt/data/v1/` (`/domains/` devolve 200) | **Não verificada** | Série e licença por confirmar |
| DGT CAOP 2025 | GeoPackage (3 zips) | **Licença não declarada** nas páginas lidas (página CAOP e condições de utilização); serviço eportugal indica gratuito | Pedir esclarecimento / citar fonte; não redistribuir ficheiros no repositório até confirmar |
| PORDATA | Sem API nem bulk encontrados | Direitos de autor FFMS, sem licença aberta nas condições (atualizadas 19.07.2024) | Não usar como fonte primária |

## 2. Cobertura (observada, não presumida)

| Dimensão | Preço venda (0012234) | Renda (0014698) | Rendimento (0012741) | Ganhos (0012656) |
|---|---|---|---|---|
| Período | 2019T4–2026T2 (trim., janela 12 m) | 2020–2025 (anual) | 2018–2024 (anual) | 2021–2024 |
| Municípios com valor | 286→304 /308 | 222→247 /308 | 297–299 /308 | 308 /308 |
| Janela comum com os restantes | 2020–2024 | 2020–2024 | 2020–2024 | só 2021–2024 |

Janela comum **compra** (preço + rendimento): 2019–2024. Janela comum **arrendamento** (renda + rendimento): 2020–2024. Séries legadas (preço 2016T1–2021T3, Metod. 2018, NUTS 2013; rendimento 2015–2021, NUTS 2013; renda 2017–2023) poderiam alargar o histórico, mas só se um teste de ligação nas sobreposições (preço 2019T4–2021T3; rendimento 2018–2021) o justificar. Não se misturam definições sem esse teste.

## 3. Riscos metodológicos (os 12 pedidos)

| # | Risco | Avaliação | Mitigação proposta |
|---|---|---|---|
| 1 | Ganhos por local de trabalho vs. rendimento por residência | `0012656` (Quadros de Pessoal, trabalhadores por conta de outrem): base geográfica **não confirmada**. `0012741` (dados fiscais da AT, por agregado fiscal): o INE não indica nos metadados lidos se a base é residência fiscal ou outra. Definições INE (metadados `0012741`, lidos a 2026-11-22): *agregado fiscal* = agregado familiar definido para efeitos de IRS (cônjuges/unidos de facto e dependentes, etc.); *rendimento bruto declarado* = rendimento não isento antes das deduções específicas nas categorias A e H, e líquido dessas deduções nas restantes categorias; *IRS liquidado* = coleta líquida das deduções e benefícios fiscais, antes de retenções na fonte e pagamentos por conta. | Rendimento principal = `0012741`, rotulado sem afirmar residentes/trabalhadores; `0012656` só como sensibilidade, rotulada |
| 2 | Média vs. mediana | `0012656` é média; `0012741` é mediana | Preferir mediana; reportar média só como contraste |
| 3 | Bruto vs. líquido | `0012741` = rendimento bruto declarado (definição INE, mistura de bruto e líquido de deduções específicas por categoria) **menos IRS liquidado**; contribuições para a Segurança Social não mencionadas → não é rendimento disponível | Chamar «rendimento declarado após IRS»; não designar «disponível» |
| 4 | Preços de transação vs. anúncios | INE usa transações (fonte fiscal/registo); não há listagens | Documentar; não misturar com portais |
| 5 | Rendas de novos contratos vs. stock | Só novos contratos disponíveis; stock **não investigado** | Interpretar como custo de entrada no mercado, nunca como renda paga pelos inquilinos existentes |
| 6 | Tipologia/dimensão/composição | €/m² mediana ≠ preço da casa típica; área média por município **N** | Duas métricas: m² por ano de rendimento (sem pressuposto) e preço-para-rendimento com área de referência explícita e sensibilidade |
| 7 | Séries, NUTS e metodologia | Metod. 2018→2022 (preço), 2021→2026 (renda); NUTS 2013/2024/geografia 2025 | Série única por métrica; chave `geocod` mapeada a CAOP 2025; testes de ligação antes de qualquer união |
| 8 | Supressão/lacunas | Renda: 20–28 % dos municípios sem valor; os sem renda têm preço e rendimento medianos mais baixos (fase 4); a dimensão do mercado **não foi medida** (não aleatório) | Indicador de cobertura; arrendamento municipal só como subconjunto; base NUTS III |
| 9 | Datas de divulgação/referência | Rendimento atualizado 2026-07-24 (ref. 2024); preço 2026-10-23 (ref. 2026T2); renda 2026-09-29 (ref. 2025) | Alinhar por ano civil de referência; preço = valor 12 m a T4 |
| 10 | Correlações geográficas por composição | Sim, para clustering/correlações (ex.: turismo, segundas habitações, compradores não residentes — o INE publica preços por domicílio fiscal do comprador) | Reportar apenas padrões descritivos; controlar/estratificar quando possível |
| 11 | Afirmações individuais | Só dados agregados | Redigir como «mediana local», nunca «uma família típica consegue…» |
| 12 | Janelas móveis sobrepostas | `0012234` é 12 m móvel → autocorrelação artificial | Usar T4 anual ou não sobreposto para inferência/mudança de regime |

Riscos adicionais:
- **R-RENT**: fontes secundárias (Montepio, Idealista, DN; não primárias) indicam que a publicação das rendas foi suspensa em 2025 e retomada a 2026-06-26 com série revista (~+50 % de contratos, mediana pouco alterada). A existência de indicadores «Metodologia 2026» atualizados em 2026-06-26/2026-09-29 é consistente com isto (verificado), mas a descrição e magnitude **não foram confirmadas no texto INE**. Usar apenas a Metod. 2026.
- **R-COUNT**: o indicador de transações (`0012785`) não tem nível municipal → não há ponderação nem limiar de tamanho de amostra por município.
- **R-INFER**: os valores publicados são medianas sem intervalos de confiança → comparações estatísticas formais entre municípios não são possíveis; só descritivas/robustez.

## 4. Rasto afirmação → fonte

| Afirmação | Evidência | Como foi verificada | Confiança |
|---|---|---|---|
| INE API é aberta, sem chave, CC BY 4.0 | `xpgid=ine_api_v2`, `ine_api_db&INST=779839468`, `ine_cont_inst&INST=3585857` | Páginas lidas | Alta |
| Preço 12 m municipal 2019T4–2026T2, 286→304/308 | `pindica.jsp?op=2&varcd=0012234&Dim1=T`, categoria Total | Sonda 2026-11-22 | Alta |
| Renda M2026 2020–2025, 222→247/308 | `varcd=0014698` | Sonda | Alta |
| Rendimento mediano por agregado 2018–2024, 297–299/308 | `varcd=0012741` | Sonda | Alta |
| Transações sem nível municipal | `varcd=0012785`: só geocod de 1–2 car. | Sonda | Alta (para esta série) |
| Rendas retomadas em jun-2026 com série revista | Montepio/Idealista (pesquisa) + datas de atualização INE | Parcial | **Média** |
| CAOP 2025 só GeoPackage | Página DGT | Lida por subagente | Média-alta |
| CAOP licença não declarada | Páginas DGT lidas | Ausência de texto | Média |
| BPstat API existe | `GET /data/v1/domains/` → 200 | curl | Alta (existência); séries N |
| Base geográfica do rendimento (residência fiscal ou outra) | Metadados INE (`minfo.jsp?var_cd=0012741`, 2026-11-22) definem agregado fiscal, rendimento bruto declarado e IRS liquidado, mas **não** a base geográfica | **Por confirmar** (publicação INE `ERendimentoNL2024.pdf` não lida) | — |

## 5. Decisão

**Opção A com restrição de âmbito (A para compra, B para arrendamento).**

- Compra municipal é viável: preço (~93–99 % dos municípios) e rendimento mediano por agregado (~97 %) com definições compatíveis em 2019–2024, em NUTS 2024 e uma única geografia de 308 municípios.
- Arrendamento municipal **não** é suficientemente completo (72–80 %, com seleção por tipo de mercado) → análise de rendas a **NUTS III** como principal; municipal só para o subconjunto com dados, assinalando o enviesamento.
- Não há justificação para estreitar a pergunta (opção C), mas há três limites a declarar: rendimento ≠ disponível; €/m² ≠ preço de casa; renda de novos contratos ≠ renda paga.

**Primeiro marco mínimo:** camada de dados reprodutível (308 municípios, 2019–2024: preço T4, rendimento mediano, renda M2026), relatório de qualidade/cobertura, chave CAOP 2025, e **duas** métricas descritivas (m² por ano de rendimento; preço-para-rendimento com 80 m² e sensibilidade), sem dashboard.

## 6. Questões em aberto (aguardam resolução)

1. Confirmar a base geográfica do rendimento local (ler a publicação INE «Estatísticas do rendimento ao nível local 2024», ISSN 2184-7177, ou pedir ao INE).
2. Identificar área média por município (Censos 2021) e série IPC.
3. Identificar a série BPstat de juros de crédito à habitação e a sua licença.
4. Esclarecer licença CAOP junto da DGT.
5. Confirmar com texto INE a revisão metodológica das rendas (2026).
