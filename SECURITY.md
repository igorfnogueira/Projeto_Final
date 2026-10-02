# Segurança — trava de segredos para agentes

Este arquivo nunca contém valor real de segredo, token ou chave — só
nomes de variável, caminhos e descrição do mecanismo. Ver
`docs/TROUBLESHOOTING.md` para causas raiz e limitações conhecidas.
Antes de lançar algo novo, rodar `docs/CHECKLIST_LANCAMENTO.md`.
Pra reduzir erro humano de copiar `.env` entre ambientes, ver
`docs/GESTOR_DE_SEGREDO.md`.

## O que existe

`governanca/guard_secrets.py` (cópia versionada, com testes em
`governanca/tests/test_guard_secrets.py`, `pytest governanca/tests`)
decide `allow` / `ask` / `deny` para chamadas de agente de IA
(Claude Code e Cursor) que envolvam:

- **Leitura de `.env` real** (`Read`, `Edit`, `Write`, `Grep`, `Glob`,
  e via caminho citado em comando de shell) — `deny`. Seguros:
  `.env.example`, `.env.sample`, `.env.template`.
- **`.envrc`** — mesmo tratamento de `.env` real, tanto por caminho
  quanto em comando de shell.
- **Comando de shell citando** `SERVICE_ROLE`, `sb_secret_`,
  `SUPABASE_SERVICE`, `dotenv_values`, `load_dotenv`,
  `create_client(...)` — `ask`.
- **Importador sem `--dry-run`** (`import_resultados.py`,
  `import_mapeamento.py`) — `ask`, regra específica de projetos que
  usam esse padrão.

`allow` é o resultado implícito (o hook não decide, nada é impresso) —
mantém read/write comuns sem fricção.

## Onde está ligado

- **Claude Code**: hook `PreToolUse` em `~/.claude/settings.json`
  (nível de usuário — não versionado neste repo), com matcher
  `Bash|PowerShell|Read|Grep|Glob`.
- **Cursor**: hooks `beforeReadFile` / `beforeShellExecution` /
  `beforeTabFileRead` em `~/.cursor/hooks.json` **de nível de
  usuário**, `failClosed: true`.

**Decisão deliberada:** o `.cursor/hooks.json` **deste repositório**
(o que é commitado e copiado para projetos novos via
`new-project.ps1`) **não** aponta para `guard_secrets.py`. Um hook
`failClosed` com caminho absoluto de uma máquina específica quebraria
qualquer colega, CI ou agente na nuvem sem esse script instalado. A
trava real, hoje, só existe no nível de usuário de quem a configurou —
não é herdada automaticamente por quem clona este template. Uma versão
portável (script versionado, caminho relativo, sem `failClosed`) é uma
decisão separada, ainda não tomada.

## Camadas versionadas no repositório (herdadas por projeto novo)

- **`.claude/settings.json`: `permissions.deny` nativo do Claude Code.**
  Nega `Read` de `.env` e variantes reais, `.mcp.json`,
  `.infisical.json`, `*.pem`, `*.key`, `~/.ssh`, `~/.aws` e
  `~/.config/gcloud`. `.env.example` fica legível. Não depende de
  script. Limite: vale para as ferramentas nativas do Claude (Read e
  afins), **não** para um `cat`/`rg` no Bash. O Bash depende da trava
  acima e da regra de segredo por nível (`.env.example`).
- **gitleaks no `.githooks/pre-commit`** varre o conteúdo staged em todo
  commit, qualquer nível. Com achado, mostra arquivo e linha com o valor
  `REDACTED`, e aborta. Sem o binário instalado, aborta também (falha
  fechada). Falso positivo: allowlist com motivo em `.gitleaks.toml`.
  O job `segredo` do CI roda o mesmo scanner no histórico, para cobrir
  quem commitou sem hook.
- **Sem sandbox nativo no Windows.** O sandbox de Bash do Claude Code
  roda só em macOS, Linux e WSL2 ("Native Windows is not supported",
  documentação oficial). No Windows nativo, o Bash do agente enxerga o
  disco inteiro. Isolamento real exigiria rodar o Claude no WSL2 —
  caminho não adotado neste template (ver ADR-0005; a estrutura de
  devcontainer que cobria isso foi movida para `template_container`
  como referência, fora do fluxo ativo).

## Limitações conhecidas (não corrigíveis só com o hook)

- **Cursor grava o conteúdo do arquivo no próprio log de depuração de
  hooks**, mesmo quando a leitura é negada — ver
  `docs/TROUBLESHOOTING.md`. Sem correção do nosso lado; reportado ao
  Cursor.
- **`@menção` de arquivo no chat do Cursor** entrega o conteúdo direto
  no contexto do agente, sem passar por nenhum hook — mitigado só por
  `.cursorignore` **por projeto** (não vem por padrão deste template;
  precisa ser criado em cada repo que use o Cursor). Observação de um
  E2E anterior: o comportamento pode variar por versão ou por contexto.
- **Varredura genérica passa pela trava.** Um agente rodando por conta
  própria `rg --hidden --no-ignore` na pasta inteira encontra o valor
  de um `.env`, porque o comando não cita `.env` e dá `allow`. Qualquer
  `.env` dentro da pasta do projeto deve ser tratado como legível pelo
  agente. Na pasta, só credencial de dev descartável (ver `.env.example`).
- **`infisical run` tira o segredo do disco, não do alcance de um
  agente no host.** Com o CLI logado, um agente com shell na mesma
  máquina pode rodar `infisical export` ou ler o ambiente do processo,
  e a trava não tem regra para `infisical`. Não medido.
- **`beforeTabFileRead`** (autocompletar inline) não dispara nesta
  versão do Cursor testada, para nenhum arquivo — não há hook
  funcional cobrindo essa superfície hoje.
- **Leitura via shell** (`Get-Content`, `cat`, `type`, `ReadAllText`
  etc.) depende de quem está na tela **rejeitar** o prompt de `ask` —
  não é bloqueio automático.
- O hook lê **texto** do comando, não o que um script faz por dentro
  (ex.: `python import_resultados.py` carrega o `.env` sozinho sem
  citá-lo no comando).

## Se um segredo real vazar

1. Rotacionar a chave imediatamente (painel do provedor — nunca só
   "confiar" que não foi usada).
2. Tratar qualquer lugar onde o valor possa ter sido persistido em
   texto puro como comprometido: histórico de terminal, logs locais de
   agente (Claude Code, Cursor), capturas de tela, clipboard.
3. Registrar o incidente em `docs/TROUBLESHOOTING.md` (causa raiz) e,
   se houver decisão de processo nova, em `docs/adr/`.
