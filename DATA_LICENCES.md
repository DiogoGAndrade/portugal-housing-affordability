# Licenças e atribuição dos dados

Verificado nas fontes oficiais em 2026-11-22 (detalhe em `docs/audit_consolidation.md`). O código e a documentação própria deste repositório estão sob licença MIT (ver `LICENSE`); esta nota trata apenas dos dados e das geometrias de terceiros, que **não** são cobertos pela MIT.

## INE — Instituto Nacional de Estatística

- Indicadores usados: `0012234` (preço de venda), `0014698` (renda de novos contratos), `0012741` (rendimento por agregado fiscal), `0014642` (IPC, base 2025), mais as séries legadas `0009490` e `0009953` (só em testes de comparabilidade) e os indicadores de sensibilidade `0012712` e `0012757`.
- Licença: **CC BY 4.0** (condições de utilização do portal do INE e página da API).
- Obrigações: citar «Fonte: Instituto Nacional de Estatística – Portugal (Statistics Portugal)», identificar a informação estatística e o período de referência, e indicar quando os dados são modificados.
- Neste projeto: os valores publicados são os do INE, sem alteração; as métricas (I1–I6, preço real) são **cálculos do autor**. Os valores NUTS III são os publicados pelo INE, não derivados de municípios. Período de referência e data de atualização de cada indicador: `data/manifests/ine_manifest.json` e lista de fontes do dashboard.

## DGT — Direção-Geral do Território

- Recurso: CAOP 2025 (Continente, Açores, Madeira). Licença: **CC BY 4.0**.
- Obrigação: ao publicar informação geográfica da DGT, mesmo parcialmente adaptada, incluir o texto «Informação geográfica cedida pela Direção-Geral do Território».
- Neste projeto: a geometria foi **simplificada** para visualização; os ficheiros originais não estão no repositório (`data/raw/caop`, ignorado) e a sua proveniência está em `data/manifests/caop_manifest.json`.

## Banco de Portugal (BPstat) — não usado em resultados publicados

Não foram encontrados termos de reutilização do BPstat (as páginas lidas não os apresentam). Por isso nenhum resultado derivado de séries BPstat consta do dashboard, dos relatórios ou do README. O código mantém uma análise local opcional (`python -m housing_pt.phase4 --with-bpstat`), que escreve para `reports/local/` (ignorado pelo Git).

## Eurostat

Referido apenas na documentação de fontes; nenhum dado do Eurostat é usado em resultados publicados.
