# Gestor de segredo dedicado (Infisical) — por que e como adotar

## Por que não só `.env` manual

`guard_secrets.py` (`SECURITY.md`) impede o **agente de IA** de ler
segredo real sem confirmação — mas não resolve o erro humano de
"copiar a chave certa no lugar certo, em todo ambiente, toda vez".
Esse é o padrão real por trás de mais de um incidente já registrado
neste template (`docs/TROUBLESHOOTING.md`): captura de tela com
segredo visível, log de ferramenta de terceiro persistindo conteúdo em
texto puro. Um gestor de segredo dedicado não elimina esse risco
sozinho, mas reduz a superfície: a chave existe num único lugar
(Infisical), sincronizada automaticamente pros ambientes reais
(Vercel, Railway, etc.) — sem `.env` copiado à mão entre máquina,
projeto e ambiente.

## Por que Infisical, e não Doppler/1Password

- **Infisical**: tier grátis generoso, self-host opcional (open
  source), CLI direto — melhor ponto de entrada pra quem está sozinho,
  sem custo fixo mensal enquanto o projeto é pequeno.
- **Doppler**: mais "zero-ops" se o projeto crescer (mais integrações
  prontas), mas sem tier gratuito tão generoso quanto o do Infisical.
- **1Password CLI**: só compensa se você já usa 1Password no dia a dia
  (login pessoal) — aí vira "uma ferramenta a menos pra gerenciar", em
  vez de mais uma conta nova.

Reavaliar se o contexto mudar (equipe crescer além de você sozinho,
custo do tier grátis deixar de compensar).

## Quando é obrigatório

Sempre que houver **credencial de produção na máquina de dev**
(service_role, token de deploy, chave de pagamento). Um `.env` dentro
da pasta do projeto é legível por qualquer agente com shell no host. A
trava de hook não cobre uma varredura da pasta inteira. Na pasta fica
só credencial de dev descartável (ver `.env.example`).

O Infisical tira o segredo do **disco**, não do alcance de um agente com
shell **no host**. Com o CLI logado, esse agente pode rodar
`infisical export` ou ler o ambiente do processo.

Para o dia a dia não mudar, ponha o prefixo no script uma vez só:

```json
"scripts": { "dev": "infisical run -- next dev" }
```

Cuidado com ferramenta que grava `.env` na pasta: pela documentação da
Vercel, o `vercel env pull` escreve `.env.local` com os segredos do
ambiente escolhido. Com
Infisical, puxe do Infisical via `infisical run` em vez de usar
`vercel env pull` para produção.

## Adoção — passo a passo

1. **Conta**: criar em [infisical.com](https://infisical.com) (grátis)
   — só você faz esse passo, não delegável.
2. **CLI**: instalar (`brew install infisical/get-cli/infisical` no
   Mac, ou via `scoop`/instalador direto no Windows — ver [docs
   oficiais](https://infisical.com/docs/cli/overview) pro comando
   exato da sua máquina).
3. **Login**: `infisical login` (abre navegador pra autenticar).
4. **Inicializar no projeto**: na raiz do projeto, `infisical init` —
   escolhe o projeto Infisical correspondente, gera `.infisical.json`
   (referência ao projeto, **sem segredo dentro** — seguro de
   commitar, mas confirmar antes de qualquer commit, mesma disciplina
   de sempre).
5. **Rodar localmente com segredo injetado**: `infisical run --
   <comando>` (ex.: `infisical run -- npm run dev`) — injeta as
   variáveis como ambiente do processo, sem nunca escrever um `.env`
   real em disco.
6. **Sincronizar pra produção**: no painel Infisical, aba
   Integrations → Secret Syncs, apontar pro Vercel/Railway/etc. —
   sincroniza automaticamente quando o segredo muda, sem copiar à mão.

## Nota — login via machine identity (Universal Auth)

Login de usuário (`infisical login`, fluxo por navegador) pode travar
em alguns terminais Windows: o prompt "paste your browser token here"
(fallback quando o callback local `localhost:<porta>` não recebe
resposta do navegador) não aceita paste nem digitação em alguns
consoles (reproduzido em PowerShell e cmd.exe nesta máquina,
2026-09-29). Se acontecer, contornar com login por **machine identity
(Universal Auth)**, que não depende desse prompt:

1. No painel web (`app.infisical.com`, login funciona normal por lá) →
   Organization Settings → Access Control → Machine Identities → criar
   identidade com método Universal Auth → gerar Client ID/Secret →
   adicionar a identidade ao projeto (Project Settings → Access
   Control).
2. No terminal:
   ```
   infisical login --method=universal-auth --client-id="..." --client-secret="..." --silent --plain
   ```
   copia o token impresso e define `INFISICAL_TOKEN` na sessão do
   terminal (`$env:INFISICAL_TOKEN = "..."` no PowerShell — **não**
   `set` do cmd, são variáveis de ambiente por processo, não
   compartilhadas entre PowerShell e cmd nem entre janelas).
3. `infisical init` também não funciona com só o token — ele precisa
   de sessão de usuário pra listar orgs/projetos interativamente. Como
   contorno, criar `.infisical.json` manualmente na raiz do projeto
   (formato documentado em
   [project-config](https://infisical.com/docs/cli/project-config)):
   ```json
   {
       "workspaceId": "<project-id-do-painel-web>",
       "defaultEnvironment": "dev"
   }
   ```
   (Project ID visível na URL do projeto no painel web ou em Project
   Settings → General. Não é segredo, mas é específico da sua conta —
   não commitar um ID real neste doc do template.)
4. **Limitação conhecida, por design**: autenticado via machine
   identity, o CLI **não** autodetecta o projeto do `.infisical.json`
   sozinho — `--projectId` é obrigatório em todo comando
   (`infisical secrets --projectId=... --env=dev`, idem pra `run`/
   `export`). Isso só é dispensável em login de usuário normal. Pra
   automatizar no dia a dia, embutir o `--projectId` no próprio script
   (`"dev": "infisical run --projectId=<id> --env=dev -- next dev"`)
   em vez de tentar fazer o CLI adivinhar.

## O que muda no checklist de lançamento

Adicionar a `docs/CHECKLIST_LANCAMENTO.md` (quando o projeto adotar
isso): confirmar que a sincronização automática está ativa antes de
assumir que a produção tem a chave mais recente — sync manual
esquecido é a mesma classe de erro que isso tudo existe pra evitar.

Fontes: [Infisical CLI Quickstart](https://infisical.com/docs/cli/usage) · [Infisical + Vercel](https://infisical.com/blog/vercel-environment-variables) · [EnvManager — Infisical Pricing](https://envmanager.com/blog/infisical-pricing)
