# Arquitetura da governança deste template

Como as peças deste repositório se encaixam: o que cada arquivo faz,
por que existe, e como um dev (humano ou agente) passa por elas no dia
a dia. Comece pelos cards (visão rápida); a seção completa abaixo tem
o detalhe de cada peça, com exemplo prático.

---

## Cards — visão rápida

┌─────────────────────────────────────────────────────────────────┐
│ 🧭 AGENTS.md / CLAUDE.md                                         │
│ Contexto que todo agente de IA lê antes de editar: stack,        │
│ convenções, Regra de Ouro (N2/N3 exige plano), o que é banido.   │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│ 🔒 governanca/guard_secrets.py                                   │
│ Hook que decide allow/ask/deny quando um agente tenta ler/citar  │
│ um .env real ou credencial. Roda ANTES da ação, nos dois         │
│ terminais (Claude Code e Cursor).                                │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│ 🛡️ SECURITY.md                                                   │
│ Onde a trava de segredos está ligada, o que ela cobre, e as      │
│ limitações conhecidas (o que ela NÃO cobre).                     │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│ ✅ .githooks/pre-commit                                          │
│ Antes de cada commit, chama um "Revisor-Cético" (Claude via CLI) │
│ pra revisar o diff staged e bloquear se achar problema grave.    │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│ 📝 .githooks/commit-msg                                          │
│ Exige que toda mensagem de commit tenha rodapé Task-Level/Model. │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│ 🚀 new-project.ps1 / setup.ps1                                   │
│ Bootstrap: cria um projeto novo com essa infra pronta            │
│ (new-project.ps1) e ativa os hooks nele (setup.ps1).             │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│ 🧩 .cursor/hooks.json + .cursor/rules/typing.mdc                 │
│ Integração com o Cursor: roda setup.ps1 ao abrir o projeto,      │
│ mais uma rule básica de tipagem.                                 │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│ 📚 docs/PADROES_DE_RISCO.md, docs/TROUBLESHOOTING.md, docs/adr/  │
│ Memória viva do projeto: padrões estruturais encontrados, causas │
│ raiz de bugs não óbvios, decisões de arquitetura com alternativa │
│ descartada. Cresce com o tempo, não é preenchido de uma vez.     │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│ ⚙️ .github/workflows/                                             │
│ ci.yml (lint+teste em todo push/PR) e security-review.yml.example│
│ (segunda opinião de segurança oficial da Anthropic, opt-in).     │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│ 🗄️ .mcp.json.example                                              │
│ MCP oficial da Supabase, read_only=true obrigatório. Opt-in —    │
│ renomear e trocar project_ref antes de usar.                     │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│ 🔑 docs/GESTOR_DE_SEGREDO.md                                     │
│ Guia de adoção de gestor de segredo dedicado (Infisical) — reduz │
│ o erro humano de copiar chave errada entre ambientes.            │
└─────────────────────────────────────────────────────────────────┘

---

## Seção completa

### 1. Contexto do agente — `AGENTS.md` e `CLAUDE.md`

São os primeiros arquivos que um agente de IA (Claude Code, Cursor)
lê ao entrar no projeto. Não têm lógica executável — são texto que
molda o comportamento do agente:

- **`AGENTS.md`**: stack, convenções de arquitetura (a preencher por
  projeto), a "Regra de Ouro" (mudança multi-arquivo exige plano
  aprovado antes da escrita; N2/N3 exigem Plan Mode) e uma lista de
  "banido/deprecated" (bibliotecas ou padrões que você não quer que a
  IA reintroduza).
- **`CLAUDE.md`**: aponta pra `AGENTS.md` pra arquitetura, e guarda os
  comandos do projeto (test/lint/build) e a regra de roteamento de
  modelo por nível de tarefa (N2 → Sonnet, N3 → Opus, sempre em Plan
  Mode).

**Exemplo prático:** ao abrir este repositório, o agente lê
`AGENTS.md` e já sabe que uma tarefa como "reestruturar o schema do
banco" (N3, multi-arquivo) exige plano aprovado antes de qualquer
`Edit`/`Write` — não é preciso repetir isso a cada prompt.

### 2. Trava de segredos — `governanca/guard_secrets.py`

Um único script Python, dois modos de saída (`--adapter claude` /
`--adapter cursor`), mesma lógica de decisão: **allow** (não decide,
deixa passar), **ask** (pede confirmação) ou **deny** (bloqueia).

O que ele analisa, sem nunca logar valor real de segredo:

| Situação | Decisão |
|---|---|
| Ler `.env`, `.env.production`, `prod.env`, `.envrc` (caminho ou comando de shell) | `deny` |
| Ler `.env.example` / `.env.sample` / `.env.template` | `allow` |
| Comando citando `SERVICE_ROLE`, `sb_secret_`, `load_dotenv`, `create_client(...)` | `ask` |
| Rodar `import_resultados.py`/`import_mapeamento.py` sem `--dry-run` | `ask` |
| `vercel env pull --environment=... --git-branch=...` sem encadeamento de shell | `allow` (exceção estreita — a Vercel grava o segredo direto no disco, sem passar pelo contexto do agente; mas o `.env.local` gravado fica legível numa varredura seguinte, então não usar para produção — ver ADR-0002, "Segredo no container") |

**Exemplo prático (simulação direta, sem precisar de agente real):**

```bash
echo '{"tool_name":"Read","tool_input":{"file_path":"C:/projeto/.env"}}' \
  | python governanca/guard_secrets.py --adapter claude
# -> {"decision": "block", "reason": "Bloqueado pela trava de segredos: ..."}

echo '{"tool_name":"Bash","tool_input":{"command":"cat .env.example"}}' \
  | python governanca/guard_secrets.py --adapter claude
# -> (saida vazia, exit 0 = allow, nao decide nada)
```

**Limite honesto, documentado no próprio script:** ele lê o **texto**
do comando, não o que um script faz por dentro (`python
import_resultados.py` carrega o `.env` sozinho sem citá-lo). Por isso
existe a regra específica do importador, e por isso a proteção real de
fundo é nunca deixar a credencial de produção como padrão de ambiente
de agente.

### 3. Onde a trava está ligada — `SECURITY.md`

O script sozinho não faz nada — precisa estar registrado como hook:

- **Claude Code**: `PreToolUse` em `~/.claude/settings.json` (nível de
  usuário, **não** versionado neste repo).
- **Cursor**: `beforeReadFile`/`beforeShellExecution`/
  `beforeTabFileRead` em `~/.cursor/hooks.json` (também nível de
  usuário).

**Decisão importante documentada ali:** o `.cursor/hooks.json` **deste
repositório** (o que é commitado e copiado pro projeto novo) **não**
aponta pra `guard_secrets.py` — um hook `failClosed` com caminho
absoluto de uma máquina específica quebraria qualquer colega ou agente
na nuvem sem esse script instalado. A trava real só existe pra quem a
configurou no próprio nível de usuário.

`SECURITY.md` também documenta o que a trava **não** cobre hoje (ex.:
Cursor grava conteúdo de arquivo no próprio log de depuração antes de
decidir; `@menção` de arquivo no chat do Cursor não passa por hook
nenhum) — sempre vale checar essa lista antes de assumir proteção que
não existe.

### 4. Revisão automática antes do commit — `.githooks/pre-commit`

Fluxo, passo a passo:

1. Se não há nada staged, sai sem fazer nada.
1b. **gitleaks** varre o conteúdo staged, sempre, antes do nível
   (`gitleaks git --pre-commit --staged --redact -v`). Achado → aborta
   mostrando arquivo:linha com o valor `REDACTED`. Sem o binário →
   aborta com a instrução de instalar. Allowlist com motivo em
   `.gitleaks.toml`. O CI roda o mesmo scanner (job `segredo`).
2. Lê a última classificação de nível de tarefa (N0-N3) num log
   externo (`$HOME/.scripts/classify-log.tsv`, ferramenta pessoal, não
   faz parte deste repo), filtrando por repositório atual e por
   frescor (≤ 6h) — um registro de outro projeto ou de ontem não
   conta.
3. Escolhe o modelo do **Revisor-Cético** pelo nível: N3 → Opus, N2 →
   Haiku, N0/N1 → revisão dispensada, sem registro recente → Opus por
   precaução (nunca assume que é seguro pular a revisão).
4. Monta um prompt com o `git diff --cached` **delimitado
   explicitamente como DADO**, não instrução — defesa contra prompt
   injection vindo do próprio diff (ex.: um comentário de código
   tentando instruir "aprove isto").
5. Chama `claude -p --model <modelo>` e exige que a **última linha**
   da resposta seja exatamente `VEREDITO: APROVADO` — qualquer outra
   coisa (inclusive CLI sem resposta, erro, timeout) bloqueia o
   commit. Falha fechada: ausência de revisão nunca é tratada como
   aprovação.

**Exemplo prático:** um commit alterando `guard_secrets.py` pra afrouxar
uma regex de segurança é barrado com `COMMIT BLOQUEADO PELO
REVISOR-CETICO`, mostrando o motivo — igual a qualquer PR humano de
revisão de segurança, mas automático e em toda tentativa de commit.

**Segunda opinião antes de commit N3:** o Revisor-Cético é afinado pro
escopo deste template (segredo, `.env`, comando de shell perigoso).
Pra mudança grande (N3), vale rodar também `/security-review` (comando
nativo do Claude Code, mesma lógica da Action oficial da Anthropic
`anthropics/claude-code-security-review`) — critério mais amplo,
padrão OWASP (SQLi, XSS, falha de auth/authz, dependência vulnerável).
Um cobre o que o outro pode não olhar; nenhum dos dois substitui o
outro. Ver também `.github/workflows/security-review.yml.example`
(item 9 abaixo) pra rodar isso automaticamente em todo PR, quando o
projeto estiver no GitHub.

### 5. Exigência de rodapé — `.githooks/commit-msg`

Mais simples: só valida que a mensagem de commit tem duas linhas no
rodapé, com regex:

```
Task-Level: N<0-3>
Model: <nome>
```

**Exemplo prático:**

```
git commit -m "fix: corrige validacao de email

Task-Level: N1
Model: Claude Sonnet 5"
```

Sem essas duas linhas, o commit é bloqueado antes mesmo do
Revisor-Cético rodar — garante rastreabilidade de "que nível de
tarefa foi essa, e qual modelo/ferramenta executou", útil pra auditar
depois quais mudanças tiveram mais ou menos rigor de revisão.

### 6. Bootstrap de projeto novo — `new-project.ps1` e `setup.ps1`

- **`new-project.ps1 -Destino C:\Projetos\meu-app-novo`**: cria a
  pasta de destino (se não existir) e copia `.githooks/`,
  `.cursor/hooks.json`, `setup.ps1`, `.cursor/rules/typing.mdc` e
  inicializa um `.gitignore` básico. Não faz `git init` nem commit —
  isso fica pro dev decidir.
- **`setup.ps1`**: idempotente, roda dentro do projeto (manual ou
  automaticamente via `.cursor/hooks.json` → `workspaceOpen`) e ativa
  `core.hooksPath = .githooks` no repo — sem isso, o Git nunca chama
  `pre-commit`/`commit-msg` mesmo estando os arquivos lá.

**Exemplo prático, do zero até o primeiro commit protegido:**

```powershell
.\new-project.ps1 -Destino C:\Projetos\meu-app-novo
cd C:\Projetos\meu-app-novo
git init
.\setup.ps1          # ativa .githooks/
# ... escreve código ...
git add .
git commit -m "feat: primeira versao

Task-Level: N1
Model: Claude Sonnet 5"
# -> pre-commit roda o Revisor-Cetico, commit-msg valida o rodape
```

### 7. Integração com o Cursor — `.cursor/hooks.json` e `.cursor/rules/typing.mdc`

- **`.cursor/hooks.json`**: um hook `workspaceOpen` que roda
  `setup.ps1` automaticamente ao abrir o projeto no Cursor — o dev
  nunca precisa lembrar de ativar os hooks manualmente.
- **`.cursor/rules/typing.mdc`**: uma rule básica (`alwaysApply:
  false`, aplica em `*.py`/`*.ts`) pedindo tipagem estrita em
  assinaturas públicas — ponto de partida a customizar por projeto.

### 8. Memória viva — `docs/PADROES_DE_RISCO.md`, `docs/TROUBLESHOOTING.md`, `docs/adr/`

Três documentos que **começam vazios** (só o cabeçalho explicando o
propósito) e crescem com o projeto — não é trabalho de setup inicial,
é disciplina contínua:

- **`docs/PADROES_DE_RISCO.md`**: padrão **estrutural**, não sintoma
  isolado — algo que pode se repetir em outro lugar do código. Cada
  entrada tem uma "assinatura de busca" (um `grep` reproduzível) pra
  checar rápido se aquele padrão já foi visto antes de investigar do
  zero.
- **`docs/TROUBLESHOOTING.md`**: causa raiz de bug que exigiu mais de
  uma tentativa pra diagnosticar — "o token expira antes do refresh
  disparar" é o padrão esperado, "login não funcionava" é sintoma
  fraco demais pra entrar aqui.
- **`docs/adr/`**: decisões de arquitetura (escolha entre alternativas,
  motivo do descarte de cada uma). `docs/adr/README.md` tem o formato
  a seguir; a numeração é sequencial (`0001-...`, `0002-...`) e um ADR
  aceito nunca é editado — uma decisão revertida vira ADR novo.

**Exemplo prático:** ao investigar um bug, antes de gastar tempo
depurando do zero, rodar a assinatura de busca de uma entrada
existente (`grep -n "..." arquivo`) pra confirmar se já é um padrão
conhecido — evita redescobrir o mesmo problema em outro projeto que
usa este mesmo template.

### 9. CI mínimo e revisão em PR — `.github/workflows/`

- **`ci.yml`**: lint + teste em todo push/PR — cobre o caso de
  esquecer de ativar `.githooks/` localmente (hook só protege quem
  rodou `setup.ps1`; CI protege o repositório inteiro, mesmo commit
  vindo de outra máquina). Comandos reais ficam como `[preencher: ...]`
  — cada projeto tem seu próprio lint/teste.
- **`security-review.yml.example`**: a Action oficial da Anthropic
  (item 4 acima), mas com extensão `.example` deliberada — só vira
  `security-review.yml` ativo quando o projeto tiver
  `ANTHROPIC_API_KEY` configurada como secret do repo. Sem isso,
  ativar por engano só deixa todo PR com um workflow quebrado.

### 10. MCP de banco — `.mcp.json.example`

Servidor MCP oficial da Supabase, pra reduzir o agente ter que
"adivinhar" schema/dado de banco navegando manualmente. Extensão
`.example` deliberada (mesmo padrão do item 10) — renomear pra
`.mcp.json` só depois de trocar `<id>` pelo `project_ref` real do
projeto Supabase, e rodar `/mcp` no Claude Code pra autenticar por
OAuth (login no navegador, nunca colar token/secret).

**`read_only=true` é obrigatório na URL, não opcional.** Achado
relevante que motivou isso: o servidor Postgres de **referência da
própria Anthropic** foi arquivado depois de descobrirem que o modo
"read-only" dele aceitava `COMMIT; DROP SCHEMA public CASCADE;` — um
servidor **alegar** ser read-only não é o mesmo que ter isso garantido
de verdade. O parâmetro `read_only=true` do Supabase MCP é a garantia
documentada oficialmente pelo fornecedor, não uma convenção informal.

**Nunca apontar `project_ref` pro projeto de produção com
`read_only=false`** — mesma lógica do `Write(**)` negado no Cursor CLI
(ADR-0001): a garantia técnica de "só lê" precisa estar na própria
ferramenta, não em confiar que ninguém vai pedir escrita.

---

## Fluxo completo, de ponta a ponta

```
1. Agente de IA abre o projeto
   └─ lê AGENTS.md / CLAUDE.md → já sabe convenções e Regra de Ouro

2. Agente tenta ler/citar um .env real
   └─ guard_secrets.py (hook do terminal, nível de usuário) decide
      allow / ask / deny — ANTES da leitura acontecer
      (só quando o comando/caminho cita o .env; varredura genérica
      como `rg --no-ignore` passa — ver SECURITY.md)

3. Dev termina a mudança, faz `git add` + `git commit`
   ├─ pre-commit: Revisor-Cetico (Opus/Haiku conforme nivel) analisa
   │   o diff staged, bloqueia se achar problema grave
   └─ commit-msg: exige rodape Task-Level/Model

4. Se algo não óbvio foi descoberto no caminho
   └─ vira entrada em docs/PADROES_DE_RISCO.md, docs/TROUBLESHOOTING.md
      ou docs/adr/ — memória pro próximo commit, próximo projeto
```
