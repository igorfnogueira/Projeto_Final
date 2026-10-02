# Como adotar este template num projeto que já existe

`new-project.ps1` assume destino vazio — ótimo pra projeto novo, mas
**não use direto** num projeto em andamento: ele copia
`AGENTS.md`/`CLAUDE.md`/`docs/*` por cima de qualquer coisa que já
exista lá com o mesmo nome, e um projeto em andamento quase sempre já
tem documentação real (README, convenções, decisões) que não pode
simplesmente ser sobrescrita.

Este guia é o caminho pra projeto **já existente**: só traz a
infraestrutura de governança (hooks, trava de segredo, revisor
automático), preservando 100% do que já está documentado — e usa o
próprio Claude Code/Cursor, com os prompts prontos abaixo, pra
preencher os campos do template com a realidade do projeto, não com
texto genérico.

---

## Antes de começar

1. **Working tree limpo** — `git status` zerado (commit ou stash) no
   projeto que vai receber o template. Se algo sair errado, você quer
   conseguir `git diff`/`git checkout` pra reverter sem misturar com
   trabalho não salvo.
2. Ter os arquivos deste template acessíveis (clonado ou copiado em
   alguma pasta local, ex.: `C:\Projetos\template_projeto`).

---

## Passo 1 — infraestrutura que quase nunca conflita (copiar direto)

Estes arquivos são mecanismo, não conteúdo — seguro copiar por cima
mesmo em projeto existente, porque um projeto sem governança
automatizada não vai ter equivalente:

```powershell
$Template = "C:\Projetos\template_projeto"   # ajuste pro seu caminho
$Projeto  = "."                               # raiz do projeto existente

Copy-Item "$Template\.githooks" "$Projeto\" -Recurse -Force
Copy-Item "$Template\.cursor\hooks.json" "$Projeto\.cursor\hooks.json" -Force
Copy-Item "$Template\.cursor\rules\typing.mdc" "$Projeto\.cursor\rules\typing.mdc" -Force
Copy-Item "$Template\setup.ps1" "$Projeto\setup.ps1" -Force
New-Item -ItemType Directory -Force "$Projeto\scripts" | Out-Null
Copy-Item "$Template\scripts\diff_docs.sh" "$Projeto\scripts\diff_docs.sh" -Force
Copy-Item "$Template\governanca" "$Projeto\governanca" -Recurse -Force
Remove-Item "$Projeto\governanca\tests\test_copier.py" -ErrorAction SilentlyContinue
```

**`governanca/tests/test_copier.py`**: apague depois de copiar (comando
acima já faz isso) se este projeto não usa Copier. Esse teste chama
`copier run_copy` contra o próprio repositório-template — copiado pra
um projeto que não é o template, ele vai falhar ou não fazer sentido
nenhum.

**Exceção — `.gitattributes`, `.gitignore` e `.gitleaks.toml`**: NÃO
sobrescrever se já existirem. Abrir os três (template e projeto) e
**acrescentar** só as linhas/entradas que faltam (ex.: `__pycache__/`,
`.pytest_cache/`, `.githooks/*.log` no `.gitignore`/`.gitattributes`;
allowlist de falso positivo já registrado no `.gitleaks.toml`). Um
projeto em andamento quase sempre já tem essas entradas específicas da
stack ou do histórico dele que você não quer perder. Se nenhum dos três
existir ainda no projeto, copiar direto do template é seguro.

## Passo 2 — ativar os hooks

```powershell
cd $Projeto
.\setup.ps1
```

Isso configura `core.hooksPath = .githooks` no repo — sem esse passo,
`pre-commit`/`commit-msg` existem no disco mas o Git nunca os chama.

## Passo 3 — os campos de texto (`AGENTS.md`, `CLAUDE.md`, `docs/`) — aqui entra o agente

Esta é a parte que **não dá pra copiar direto**: `AGENTS.md` e
`CLAUDE.md` do template têm campos `[preencher: ...]` genéricos, e o
projeto existente pode já ter um `README.md`, um `CONTRIBUTING.md`, ou
até um `AGENTS.md`/`CLAUDE.md` próprio com convenções reais. Sobrescrever
isso é o erro que este guia existe pra evitar.

Em vez de você preencher manualmente, use o próprio agente — ele já
está lendo o projeto, consegue extrair convenção real do código em vez
de você ter que lembrar/redigitar. Os prompts abaixo são pensados pra
rodar **nesta ordem**, cada um é um checkpoint (não deixe o agente
pular direto pra escrita sem te mostrar o que vai fazer).

### Prompt 1 — inventário, sem escrever nada ainda

```
Antes de trazer o template de governança pra este projeto, preciso que
você faça um inventário do que já existe, sem editar nada ainda:

1. Liste todo arquivo de documentação já existente na raiz e em docs/
   (README, CONTRIBUTING, CHANGELOG, ADRs, AGENTS.md/CLAUDE.md se já
   existirem, qualquer .md relevante).
2. Para cada um, resuma em 1-2 linhas o que ele cobre hoje.
3. Aponte especificamente: este projeto já tem CLAUDE.md ou AGENTS.md?
   Já tem CHANGELOG.md? Já tem alguma pasta docs/adr/ ou equivalente
   de decisão de arquitetura?
4. Não crie, não edite, não sobrescreva nenhum arquivo neste prompt —
   só relatório.
```

### Prompt 2 — plano de mesclagem (ainda sem escrever)

Cole o `AGENTS.md` e o `CLAUDE.md` do template (arquivo por arquivo,
ou aponte o caminho se o agente tiver acesso ao disco) junto com este
prompt:

```
Aqui estão AGENTS.md e CLAUDE.md de um template de governança que
quero trazer pra este projeto (colados/anexados acima ou no caminho
indicado). Com base no inventário que você já fez:

- Se este projeto NÃO tem AGENTS.md/CLAUDE.md: proponha o conteúdo
  preenchido (troque os campos [preencher: ...] pela convenção REAL
  deste projeto — stack detectada, padrão de pastas observado no
  código, tratamento de erro/logging já em uso). Não invente convenção
  que o código não demonstra; se não der pra inferir, deixe o campo
  como [preencher] e me avise que precisa da minha decisão.
- Se este projeto JÁ tem AGENTS.md/CLAUDE.md ou README com esse tipo
  de informação: proponha como MESCLAR (não substituir) — o que do
  template é novidade genuína (ex.: a Regra de Ouro sobre plano
  aprovado antes de mudança multi-arquivo) entra como seção nova; o
  que já existe no projeto permanece como está, sem reescrever.
- Liste também, sem aplicar ainda, o que fazer com docs/PADROES_DE_RISCO.md,
  docs/TROUBLESHOOTING.md, docs/adr/ e CHANGELOG.md do template: se o
  projeto já tem CHANGELOG.md, por exemplo, não criar um segundo —
  só adicionar entrada nova se algo mudou agora. Se não tem
  PADROES_DE_RISCO.md/TROUBLESHOOTING.md, propor criar vazio (só o
  cabeçalho) pra registrar daqui pra frente, não com histórico
  retroativo inventado.

Me mostre esse plano completo. Não escreva nenhum arquivo ainda.
```

### Prompt 3 — aplicar, com diff, um arquivo por vez

Só depois de aprovar o plano do Prompt 2:

```
Aplique o plano que você propôs, um arquivo por vez. Pra cada arquivo:
mostre o diff (ou o conteúdo completo, se for arquivo novo) antes de
gravar, e espere minha confirmação antes de ir pro próximo. Nunca use
git add . — cada arquivo tocado deve ser adicionado nomeado
explicitamente quando eu pedir pra commitar.
```

### Prompt 4 — checagem final

```
Rode um grep por "[preencher" em todo o projeto e me liste os arquivos
e linhas que ainda têm campo genérico do template não preenchido —
preciso decidir manualmente esses casos, não adivinhe.
```

(Equivalente direto no terminal, se preferir rodar você mesmo:
`grep -rn "\[preencher" .` — na raiz do projeto, depois do Passo 3.)

## Passo 4 — testar sem arriscar o trabalho real

Antes de confiar que o `pre-commit`/`commit-msg` estão funcionando,
teste com um commit descartável:

```powershell
git checkout -b teste-hooks-governanca
"teste" | Out-File zz_teste_hooks.txt
git add zz_teste_hooks.txt
git commit -m "teste: valida hooks de governanca

Task-Level: N0
Model: <nome do seu modelo>"
# Deve rodar o Revisor-Cetico e exigir o rodape Task-Level/Model.
# Depois de confirmar que funciona:
git checkout main
git branch -D teste-hooks-governanca
```

Se o `pre-commit` bloquear por falta de `claude`/`cursor-agent` no
PATH, ou o `commit-msg` rejeitar por rodapé errado, é sinal de que os
hooks estão ativos — resolva a causa (instalar CLI, ajustar mensagem)
antes de seguir com commits reais.

## Passo 5 — trava de segredos (`governanca/guard_secrets.py`)

Copiar o arquivo não ativa a trava sozinho — como documentado em
`SECURITY.md`, ela precisa estar registrada como hook no **nível de
usuário** (`~/.claude/settings.json` pro Claude Code, `~/.cursor/hooks.json`
pro Cursor), não no repo. Se você já tem isso configurado globalmente
na sua máquina, a trava já vale pra este projeto novo automaticamente,
sem passo extra aqui. Se ainda não tem, isso é configuração de
máquina, não deste projeto — foge do escopo deste guia.

---

## Passo 6 — passar a receber `copier update` (opcional, projeto já adotado por cópia manual)

Se você seguiu os passos 1-5 (cópia manual, sem Copier) e agora quer que
este projeto passe a receber `copier update` daqui pra frente, sem
recriar o repositório: crie `.copier-answers.yml` na raiz à mão,
apontando pra versão do template equivalente ao que foi copiado
(história 10 da issue #1 — caminho documentado, não automatizado):

```yaml
# .copier-answers.yml
_src_path: C:\Projetos\template-governanca
_commit: v0.1.0   # a tag do template na época em que este projeto nasceu
nome_projeto: meu-projeto-existente
stack: "[preencher: stack real deste projeto]"
usa_supabase: false
usa_infisical: false
```

Depois:

```powershell
copier update --trust
```

O Copier compara o projeto contra o conteúdo de `v0.1.0` (o que
`.copier-answers.yml` diz que já foi aplicado) e o que existe hoje no
template, e traz só a diferença — com merge de 3 vias, então uma edição
sua vira conflito explícito, não é sobrescrita em silêncio. Revise o
diff antes de commitar, do mesmo jeito que no Passo 3.

**Se o `_commit` estiver errado** (não corresponde à versão real que foi
copiada), o Copier pode propor mudanças demais ou de menos — nesse caso,
trate o resultado como um novo Passo 2 (plano de mesclagem) em vez de
aplicar direto.

## Resumo do que muda vs. `new-project.ps1`

| | Projeto novo (`new-project.ps1`) | Projeto existente (este guia) |
|---|---|---|
| `.githooks/`, `.cursor/hooks.json`, `setup.ps1`, `governanca/` | Copia direto | Copia direto (Passo 1) |
| `.gitignore`/`.gitattributes` | Cria do zero | Mescla, sem sobrescrever (Passo 1) |
| `AGENTS.md`/`CLAUDE.md` | Copia template com campos genéricos | Agente preenche com convenção real ou mescla com o que já existe (Passos 3, prompts 1-4) |
| `docs/PADROES_DE_RISCO.md`, `TROUBLESHOOTING.md`, `adr/`, `CHANGELOG.md` | Cria vazio | Só cria se não existir equivalente; nunca duplica (prompt 2) |
| Ativação | `git init` + `.\setup.ps1` | `.\setup.ps1` (repo já existe) |
