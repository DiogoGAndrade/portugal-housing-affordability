# Publicação estática do dashboard (Cloudflare Pages)

O dashboard é um site estático: a pasta `site/` contém só `index.html` (HTML, CSS e JavaScript inline, sem pedidos externos) e `_headers` (cabeçalhos de segurança). Não há passo de compilação no servidor, nem *analytics*, nem cookies, nem chamadas a APIs.

## O que é publicado
| Ficheiro | Função |
|---|---|
| `site/index.html` | página única gerada por `python -m housing_pt.dashboard`; dados do INE e geometria CAOP embebidos, com atribuição visível |
| `site/_headers` | cabeçalhos aplicados pelo Cloudflare Pages a todas as respostas (gerado pelo mesmo comando) |

`_headers` contém uma política de segurança de conteúdo (CSP) fixada por SHA-256 ao único `<script>` e ao único `<style>` da página (por isso não é preciso `unsafe-inline`), `connect-src 'none'`, `frame-ancestors 'none'`, `X-Content-Type-Options: nosniff`, `Referrer-Policy: no-referrer`, `Permissions-Policy` restritiva, `Strict-Transport-Security` e `Cache-Control` sem cache longa (a página muda quando os dados são regenerados). O HTTPS é fornecido pela plataforma. Os testes verificam que os *hashes* correspondem ao conteúdo e que a página não tem atributos `style` inline nem recursos externos.

## Publicar (manual e reprodutível)
Pré-requisito: uma conta Cloudflare e o `wrangler` autenticado (`npx wrangler login`). A CI **nunca** publica.

```powershell
npx wrangler pages project create portugal-housing-affordability --production-branch main   # só na primeira vez
npx wrangler pages deploy site --project-name portugal-housing-affordability --branch main --commit-dirty=true
```

Nota (wrangler 4.167): na primeira criação do projeto o `wrangler` pode tentar delegar para o produto Workers e falhar sem publicar nada; nesse caso repetir a criação com `--force` (só nessa primeira vez). Os comandos seguintes já correm diretamente no Pages.

O endereço de produção é `https://<projeto>.pages.dev`. Não é necessário domínio próprio; se for usado mais tarde, configura-se à parte (DNS e certificado são decisões separadas).

## Verificar após publicar
```powershell
curl -sI https://portugal-housing-affordability.pages.dev | findstr /i "content-security x-content-type referrer strict permissions"
```
Abrir a página e confirmar: introdução, mapa, pesquisa, tabela alternativa, glossário, exportação CSV, atribuições, e **nenhum erro na consola** (um erro de CSP indicaria que `index.html` e `_headers` ficaram dessincronizados: regenerar ambos com `python -m housing_pt.dashboard`).

## Reverter
No painel do Cloudflare Pages → *Deployments* → escolher uma versão anterior e «Rollback», ou voltar a executar o `deploy` a partir de um commit anterior.
