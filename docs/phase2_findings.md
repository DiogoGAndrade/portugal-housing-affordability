# Fase 2 — resolução das questões em aberto

Acedido em **2026-11-22**. Estado: **R** resolvida · **P** parcial · **A** aberta.

| # | Questão | Estado | Evidência / conclusão |
|---|---|---|---|
| 1 | Base do rendimento; definição exata | **P** | Metadados INE (lidos no navegador a 2026-11-22, `https://www.ine.pt/bddXplorer/htdocs/minfo.jsp?var_cd=0012741&lingua=PT`): definições de agregado fiscal, rendimento bruto declarado e IRS liquidado (ver `docs/audit_consolidation.md`). **A base geográfica (residência fiscal ou outra) e o tratamento da Segurança Social não são indicados.** A publicação INE (`ERendimentoNL2024.pdf`, 45 MB) não foi lida. Rótulo prudente mantido |
| 2 | Área média por município | **P** | Censos 2021 têm contagens por escalão de área útil por município, mas não média: `0012526` (arrendados), `0012524` (própria), `0012512` (**área por ocupante**, não área total). `0012524` excede o limite de linhas por defeito → extrair por período e dimensões. Área útil ≠ área usada no €/m² do INE (por confirmar). **Mantém-se A = 60/80/100 m² como pressuposto** |
| 3 | Deflator | **R** | IPC base 2025: `0014640` (mensal), `0014642` (anual), taxa de variação média 12 m `0014650`; IHPC: `0014654`/`0014656`/`0014658`. Escolha recomendada: IPC (anual, `0014642`) como deflator nacional; confirmar cobertura histórica ≥2019 e a mudança de base ao implementar |
| 4 | Juros de crédito à habitação (BPstat) | **P** | API `https://bpstat.bportugal.pt/data/v1/` funciona (redirecionamentos 301 → seguir). Domínio 186 «Loans for house purchase» (4 datasets, atualizado 2026-11-02). Séries candidatas de **taxa de juro de novos empréstimos para habitação própria permanente**: taxa fixa, percentil 50: **12710738**; taxa variável, percentil 50: **12710733** (outros percentis 12710735/34/36/39/40/41/37). Uma média agregada pode existir no domínio 21 «Interest rates» — **não procurada**. **Licença BPstat: não verificada** |
| 5 | Licença CAOP | **R** | **CC BY 4.0** (dados.gov.pt, registos CAOP2025 Continente/RAA/RAM; página DGT «dados abertos»). Atribuição: «Informação geográfica cedida pela Direção-Geral do Território». O registo SNIG não foi legível e o repositório GitHub não tem ficheiro de licença. **Descarregado em 2026-11-22 com autorização** (3 zips, ~143 MB, hashes em `data/manifests/caop_manifest.json`). Junção validada: ver secção CAOP abaixo |
| 6 | Texto INE sobre revisão das rendas (Metodologia 2026) | **A** | Mesma limitação do ponto 1. Observável: indicadores «Metodologia 2026» atualizados em 2026-06-26/09-29. Mantém-se R-RENT |
| 7 | Lacunas municipais de renda são estruturais? | **P** | Cobertura municipal cresce 222→247 de 308 (2020→2025); falta ainda por analisar perfil (população/NUTS) dos municípios sem valor. Regra de supressão INE **não encontrada** |

## Resultado novo e importante: o geocod municipal NÃO é estável entre versões NUTS

Os 7 caracteres do geocod do INE incluem um prefixo NUTS III de 3 caracteres que muda entre NUTS 2013 e NUTS 2024 (p. ex. `16B1001` → `1D11001`). Só **132 de 308** códigos coincidem diretamente. O sufixo de 4 caracteres (**DICO**, distrito + município) é estável: 308/308 coincidem e são únicos em ambas as versões. **Regra: juntar séries de versões diferentes sempre por `dico` (= `geocod[3:]`)**. A chave `geo_key` passou a incluir `dico`, que também serve para juntar ao CAOP (a verificar quando o CAOP for descarregado).

## Testes de ligação de séries legadas (`reports/linkage_report.md`)

| Série | Sobreposição | Resultado | Decisão |
|---|---|---|---|
| Rendimento mediano por agregado: `0009953` (NUTS 2013) vs `0012741` (NUTS 2024) | 2018–2021, 297–298 municípios | **Valores idênticos** (rácio 1,000; 0 % com diferença >5 %) | **Pode estender-se o rendimento a 2015–2017** (via `dico`), tratando-se da mesma série com geografia diferente |
| Preço 12 m: `0009490` (Metod. 2018) vs `0012234` (Metod. 2022) | 2019T4–2021T3, 282–291 municípios por trimestre | Correlação de postos 0,993–0,995; rácio mediano 1,000–1,005; mediana do |log-diferença| 1,4–2,2 %; **20–25 % dos municípios diferem >5 %** | **Não unir ao nível municipal na análise principal.** Ordenação preservada, mas níveis mudam em ~1/5 dos municípios; usar a série legada só como sensibilidade (2016–2019) e/ou a nível NUTS III/II após novo teste |

Consequência para o plano: a janela de compra principal mantém-se 2019–2024 (preço atual + rendimento). O rendimento pode recuar até 2015, mas sem preço comparável isso não alarga a acessibilidade; uma extensão 2016–2019 exigiria o preço legado como análise separada.

## CAOP 2025 — descarregado e validado

Ficheiros: Continente (111,6 MB), Açores (15,9 MB), Madeira (15,2 MB), em `data/raw/caop/` (ignorados pelo Git; URLs, tamanhos e SHA-256 no manifesto). Camadas de município: 278 + 16 + 3 + 11 = **308**. Campo `dtmn` = DICO.

- Junção com a chave INE por `dico`: **308/308** (0 só-INE, 0 só-CAOP).
- Nomes de NUTS III iguais nos 308 → valida a hierarquia município→NUTS III derivada dos geocodes do INE.
- Nomes de município iguais em 304; 4 diferem só no rótulo (Calheta R.A.M./R.A.A., Lagoa R.A.A., Vila da Praia da Vitória).
- Atribuição obrigatória em qualquer mapa/figura: «Informação geográfica cedida pela Direção-Geral do Território».
- Ainda não foi usada geometria (requer geopandas/pyogrio; Fase 3).

## Por resolver / próximos passos

1. Ler a ficha metodológica do INE (rendimento e rendas) no navegador ou pedir ao INE; até lá, os rótulos prudentes mantêm-se.
2. Decidir a série de juros (percentil 50 fixa/variável ou média agregada no domínio 21) e confirmar licença BPstat.
3. Obter distribuição por escalão de área (Censos 2021) por município, se se quiser calibrar A.
5. Perfilar a ausência de dados de renda (população, NUTS) para decidir a política de análise de rendas.
