# Troubleshooting

Registra causas raiz de falhas que exigiram investigação não óbvia —
não sintomas. Ver também `governanca/guard_secrets.py` e
`governanca/tests/test_guard_secrets.py` para a trava de segredos em si.

## Cursor grava o conteúdo do arquivo no próprio log de hooks, mesmo quando o hook nega a leitura

**Sintoma:** mesmo com `guard_secrets.py` negando (`deny`) corretamente
a leitura de um `.env` real via hook `beforeReadFile`, o conteúdo do
arquivo — inclusive segredo real — aparece em texto puro em disco, em
`%APPDATA%\Roaming\Cursor\logs\...\cursor.hooks.workspaceId-*.log`.

**Causa raiz:** o canal de depuração "Hooks" do Cursor grava o payload
JSON completo enviado a qualquer hook do usuário — incluindo o campo
`content` (conteúdo do arquivo lido) — **antes** de aplicar a decisão
do hook. É comportamento intencional da ferramenta de depuração do
Cursor, não um bug de `guard_secrets.py`, `~/.cursor/hooks.json` ou
`~/.claude/settings.json`. Confirmado por pesquisa: não existe
configuração de verbosidade, redação de conteúdo ou retenção
documentada para esse canal (docs oficiais do Cursor; issue aberta sem
solução em `cursor/cursor#3040` no GitHub).

**Correção aplicada (só do incidente já ocorrido):** arquivo de log com
o segredo real (`fn-grow/webapp-vercel/.env.local`) identificado e
apagado em 2026-09-22, após mapear o escopo (confinado à sessão de
teste do dia anterior, nenhuma ocorrência em sessões mais antigas). As
chaves desse projeto (`SUPABASE_SECRET_KEY`, `TELEGRAM_BOT_TOKEN`,
`SITE_PASSWORD`) precisam ser rotacionadas por fora (painel do
Supabase / BotFather) — ação manual, fora deste repositório.

**Sem correção estrutural disponível.** É uma limitação externa do
Cursor. Nenhuma configuração do nosso lado impede que o conteúdo do
arquivo seja gravado nesse log, mesmo quando a leitura é negada.

**Mitigação adotada:**
- Nunca testar a trava (`guard_secrets.py`) com `.env` real — sempre
  arquivo fictício (ex.: `zz_fake/.env` com um valor inventado).
- Checagem manual ocasional de `%APPDATA%\Roaming\Cursor\logs\` por
  entradas com `file_path` de `.env` real e campo `content` presente.
- Reportado ao Cursor como pedido de melhoria (ver `docs/adr/` se uma
  decisão formal vier a ser registrada sobre como reagir caso o Cursor
  não corrija isso).

**Pendente:** acompanhar se o Cursor passa a oferecer redação ou
retenção configurável nesse canal; revisar esta entrada se sim.

## Commit abortado: "gitleaks nao encontrado"

**Sintoma:** `git commit` aborta com "gitleaks nao encontrado -- commit
abortado".

**Causa raiz:** o `.githooks/pre-commit` falha fechado sem o binário do
gitleaks, de propósito: um hook que passa em silêncio some sem ninguém
perceber.

**Correção:** `winget install Gitleaks.Gitleaks` (Windows) ou
`brew install gitleaks` (macOS), e **reabrir o terminal**, porque o
winget só atualiza o PATH de sessões novas. `--no-verify` pula o hook
inteiro (inclusive o revisor) e deve ser exceção consciente.

## Commit abortado pelo gitleaks com falso positivo

**Sintoma:** o gitleaks acusa `RuleID`/`File`/`Line` num valor que não
é segredo (chave pública de teste, hash, exemplo de documentação).

**Correção:** acrescentar em `.gitleaks.toml` uma entrada `[[allowlists]]`
restrita (por `paths` ou `regexes`), **com um `description` explicando o
motivo**, e commitar junto. Não desligar o hook. Se for segredo real:
tirar do arquivo e rotacionar a chave, caso ela já tenha saído da
máquina.

## Revisor-Cético roda com Opus em commit N2

**Sintoma:** o pre-commit diz "Ultima tarefa classificada como N3" em
commits N2, e todo commit gasta cota de Opus.

**Causa raiz:** o `classify-hook.ps1` (hook `UserPromptSubmit`,
ferramenta pessoal em `~/.scripts`) recebe também os relatórios de
subagente e as notificações de tarefa em background, que chegam pelo
mesmo evento que a mensagem do usuário. Esses relatórios são longos e
cheios de "segurança/segredo/ADR", então viravam N3 no
`classify-log.tsv`. No caso N0/N1, o texto do subagente seria ainda
despachado ao Cursor CLI como se fosse pedido do usuário.

**Correção:** ignorar prompts que começam com `<agent-message` ou
`<task-notification` (corrigido em 2026-09-25). Uma entrada N3 antiga
continua valendo até vencer a janela de frescor de 6h.

## `new-project.ps1`/`copier` falha com "copier nao encontrado"

**Sintoma:** `new-project.ps1` sai com "Copier nao encontrado no PATH".

**Correção:** `uv tool install copier` (recomendado, já usado neste
projeto) ou `pipx install copier`. Reabra o terminal se o PATH não
atualizar na sessão atual.

## `copier update` não traz uma mudança que já está no template

**Sintoma:** editei um arquivo no template, rodei `copier update` no
projeto gerado, e a mudança não chegou — mesmo com o arquivo do
template já salvo em disco.

**Causa raiz:** `copier update` compara contra a **última tag** do
template (versão do `_commit` gravado em `.copier-answers.yml`), não
contra o working tree. Uma mudança sem tag nova não existe para o
`update`.

**Correção:** commitar a mudança no template e criar uma tag nova
(`git tag vX.Y.Z`) antes de rodar `copier update` no projeto. Para
testar uma mudança ainda sem tag (ex.: durante o desenvolvimento do
próprio template), usar `copier update --vcs-ref=HEAD` explicitamente.

## `governanca/tests/test_copier.py` aparece como "skipped", não falha nem passa

**Causa raiz:** o `copier` do `uv tool install copier` fica isolado no
venv do tool, fora do Python que o `pytest` do sistema usa. O arquivo
usa `pytest.importorskip("copier")`, que pula o arquivo inteiro sem
erro quando o import falha — fácil de ler como "sem teste de Copier
pra rodar" em vez de "faltou o import".

**Correção:** `uv run --with copier --with pyyaml pytest
governanca/tests/test_copier.py -v`.

## Primeiro commit do projeto gerado pelo Copier já exige rodapé `Task-Level`/`Model`

**Sintoma:** logo após `copier copy`, o primeiro `git commit` no
projeto novo é bloqueado por "falta 'Task-Level: N<0-3>' no rodapé",
antes mesmo de rodar `setup.ps1`.

**Causa raiz:** não é bug — `_tasks` do `copier.yml` já roda `git
config core.hooksPath .githooks` como parte da própria geração
(história 12 da issue #1: "o projeto nasce protegido"). `setup.ps1`
continua sendo copiado e é idempotente (ainda necessário pro hook
`workspaceOpen` do Cursor reativar depois de um clone novo), mas deixa
de ser o que ativa o hook pela primeira vez.

**Não é erro a corrigir:** o commit inicial de um projeto novo já
segue a mesma régua dos demais. Se isso for indesejado num caso
específico, `git commit --no-verify` é a saída consciente e visível de
sempre — não crie exceção silenciosa no hook pra isso.

## Delegação N0/N1 ao `cursor-agent -p`: "aprovado" na chamada seguinte não faz nada

**Sintoma:** `cursor-agent -p` recusa a tarefa original (ex.: por
esbarrar na Regra de Ouro de mudança multi-arquivo) e pede aprovação.
Uma segunda chamada só com `"aprovado"` responde que não há plano nem
conversa anterior — nada é alterado.

**Causa raiz:** `cursor-agent -p` é stateless entre chamadas de
processo; cada invocação não tem acesso ao que foi dito na anterior,
mesmo dentro do mesmo `--workspace`.

**Correção:** reenviar a tarefa completa numa nova chamada, incluindo
o que foi aprovado — nunca só a palavra de confirmação.

**Nota (Windows):** em algumas instalações, `cursor-agent` só está no
PATH do PowerShell, não no do Git Bash. Se a chamada via Bash falhar
com "command not found" mas `where cursor-agent` encontrar o binário,
rode via PowerShell.

## Commit abortado por `scripts/diff_docs.sh`: variável de ambiente não documentada

**Sintoma:** commit bloqueado com "ERRO: variavel(is) de ambiente
referenciada(s) no codigo mas ausente(s) de .env.example: NOME".

**Causa raiz:** o script detecta acesso a variável de ambiente
(`process.env.NOME`, `os.environ[...]`/`os.getenv(...)`, `$env:NOME`)
em arquivo de código rastreado e a compara contra `.env.example`. É a
única checagem do script que bloqueia o commit (ADR-0006) — o resto é
só relatório.

**Correção:** adicionar o nome da variável (sem valor) em
`.env.example`. Se for falso positivo — a detecção é heurística por
regex, não entende contexto (ex.: uma variável de ambiente do próprio
sistema operacional, não da aplicação) — adicionar o nome mesmo assim
resolve, já que `.env.example` só documenta nomes, não segredos.

## `infisical init` fica pedindo login de novo mesmo com `INFISICAL_TOKEN` definido

**Sintoma:** login via machine identity (Universal Auth) bem-sucedido,
`INFISICAL_TOKEN` confirmado como definido na sessão do terminal, mas
`infisical init` continua respondendo "No valid login session found,
triggering login flow" e reabre o fluxo de login por navegador.

**Investigação:** duas hipóteses testadas nessa ordem (via skill
`diagnosing-bugs`):
1. Variável de ambiente definida na janela de terminal errada —
   confirmado num primeiro caso real (`set` rodado num cmd.exe, depois
   verificado com `echo %INFISICAL_TOKEN%` numa janela PowerShell
   diferente, que imprimiu o literal `%INFISICAL_TOKEN%` sem resolver
   — prova de processos/sessões diferentes). Corrigido reproduzindo
   tudo numa única janela consistente.
2. Mesmo com a variável confirmada ("definida") na janela certa,
   `infisical init` **ainda** falhava do mesmo jeito.

**Causa raiz:** `infisical init` não suporta autenticação via machine
identity/token — o comando precisa de uma sessão de usuário
interativa pra listar orgs/projetos, independente do `INFISICAL_TOKEN`
estar correto. É comportamento do CLI (v0.43.137), não um erro de
configuração local.

**Sem correção estrutural disponível.** `init` continuará exigindo
login de usuário enquanto isso não mudar no CLI.

**Contorno adotado:** criar `.infisical.json` manualmente na raiz do
projeto em vez de rodar `init` (formato e limitação relacionada —
`--projectId` obrigatório em todo comando com machine identity — em
`docs/GESTOR_DE_SEGREDO.md`).

## `setup.ps1` relatava sucesso na instalação do plugin mesmo quando o comando falhava

Identificado em: 2026-09-30, skill `revisao-pre-producao` (escopo:
projeto inteiro).

O bloco que instala `mattpocock-skills` via `claude plugin install`
descartava o stderr (`2>$null`) e imprimia a mensagem verde de sucesso
de forma incondicional, sem checar o código de saída do comando.

**Causa raiz:** falta de tratamento do caminho de falha — só o caminho
feliz (`claude` presente no PATH) foi considerado; dentro dele, o
resultado do comando em si nunca era verificado.

**Correção (2026-09-30):** captura a saída do comando (`2>&1`) e
verifica `$LASTEXITCODE`; no caminho de erro, mostra o código de saída
e a saída real do comando, em vez de uma mensagem de sucesso genérica.
Validado nos dois caminhos: sucesso real nesta máquina e falha
simulada (função `claude` fake forçando `$LASTEXITCODE = 1`).

Assinatura de busca: `grep -n 'LASTEXITCODE' setup.ps1`.

## `date -d` na checagem de frescor do pre-commit falha silenciosamente em macOS

Identificado em: 2026-09-30, skill `revisao-pre-producao` (escopo:
projeto inteiro).

`.githooks/pre-commit` convertia o timestamp da última classificação
pra epoch com `date -d "$TS_ULTIMO" +%s` — sintaxe GNU date. Em macOS
(BSD date, sem `-d`), o comando falha e o `2>/dev/null` engole o erro;
`TS_EPOCH` fica vazio, o bloco de checagem de frescor inteiro é pulado,
e uma classificação com mais de 6h continua sendo tratada como válida
sem aviso nenhum — degrada a proteção da Regra de Ouro silenciosamente
num SO específico.

**Causa raiz:** script escrito e testado só em ambiente GNU/Linux
(Git Bash no Windows usa coreutils GNU), sem considerar BSD date.

**Correção (2026-09-30):** fallback explícito pra sintaxe BSD
(`date -j -f "%Y-%m-%d %H:%M:%S" "$TS_ULTIMO" +%s`) quando a tentativa
GNU retorna vazio. Validado nesta máquina: o caminho GNU continua
resolvendo igual (sem regressão); o caminho BSD não foi testado ao
vivo em macOS real (sem máquina disponível), só por leitura da
documentação do `date` BSD — se algum colaborador usar macOS, vale
confirmar na prática.

Assinatura de busca: `grep -n "date -j -f" .githooks/pre-commit`.
