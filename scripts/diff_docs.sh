#!/bin/sh

# Relatorio deterministico de deriva entre codigo e documentacao.
# Usado pela skill auditoria-projeto (auditoria periodica) e pelo
# .githooks/pre-commit (checagem a cada commit). POSIX sh, nao bash --
# mesma restricao de portabilidade que o proprio pre-commit ja segue
# (nao assume array nem $'...'), porque o template e agnostico de
# stack e nao pode exigir um runtime especifico so para este script.
#
# Uso: sh scripts/diff_docs.sh [dias]   (padrao: 30)
#
# Unico caso que termina em exit != 0: variavel de ambiente referenciada
# no codigo rastreado e ausente de .env.example -- e o unico item desta
# lista deterministico o bastante para travar um commit, no mesmo
# espirito do gitleaks. Todo o resto (commits do periodo, docs vs
# codigo, marcadores pendentes) e so relatorio informativo.

DIAS="${1:-30}"

if ! git rev-parse --show-toplevel >/dev/null 2>&1; then
    echo "diff_docs.sh: nao esta num repositorio git, pulando."
    exit 0
fi

REPO_ROOT=$(git rev-parse --show-toplevel)
cd "$REPO_ROOT" || exit 0

echo "== diff_docs.sh: janela de ${DIAS} dias =="

echo ""
echo "-- Commits no periodo --"
git log --oneline --since="${DIAS} days ago" 2>/dev/null

ARQUIVOS=$(git log --name-only --since="${DIAS} days ago" --format="" 2>/dev/null | sort -u | grep -v '^$')
CODIGO=$(printf '%s\n' "$ARQUIVOS" | grep -v '\.md$')
DOCS_MUDARAM=$(printf '%s\n' "$ARQUIVOS" | grep '\.md$')

echo ""
echo "-- Codigo alterado no periodo --"
if [ -n "$CODIGO" ]; then
    printf '%s\n' "$CODIGO" | sed 's/^/  /'
else
    echo "  (nenhum)"
fi

echo ""
echo "-- Docs (.md) alterados no periodo --"
if [ -n "$DOCS_MUDARAM" ]; then
    printf '%s\n' "$DOCS_MUDARAM" | sed 's/^/  /'
else
    echo "  (nenhum)"
fi

echo ""
echo "-- Documentos parados (.md sem mudanca no periodo, com codigo mudando) --"
if [ -n "$CODIGO" ]; then
    AGORA=$(date +%s)
    LIMITE=$((DIAS * 86400))
    ACHOU_PARADO=0
    for doc in $(git ls-files '*.md'); do
        ULTIMO=$(git log -1 --format=%ct -- "$doc" 2>/dev/null)
        [ -z "$ULTIMO" ] && continue
        IDADE=$((AGORA - ULTIMO))
        if [ "$IDADE" -gt "$LIMITE" ]; then
            echo "  $doc"
            ACHOU_PARADO=1
        fi
    done
    if [ "$ACHOU_PARADO" -eq 0 ]; then
        echo "  (nenhum)"
    fi
else
    echo "  (nenhum arquivo de codigo mudou no periodo, checagem pulada)"
fi

echo ""
echo "-- Marcadores pendentes (PENDENTE/TODO/FIXME) --"
MARCADORES=$(git grep -nE 'PENDENTE|TODO|FIXME' -- . 2>/dev/null)
if [ -n "$MARCADORES" ]; then
    TOTAL=$(printf '%s\n' "$MARCADORES" | wc -l | tr -d ' ')
    echo "  Total: ${TOTAL}"
    printf '%s\n' "$MARCADORES" | sed 's/^/  /'
else
    echo "  Total: 0"
fi

echo ""
echo "-- Variaveis de ambiente referenciadas no codigo vs .env.example --"
# So codigo conta: .md, o proprio script e governanca/tests ficam de
# fora, senao prosa que so MENCIONA "process.env.X" (documentacao,
# exemplo de troubleshooting) ou literal de teste (fixture que testa
# esta mesma deteccao) vira falso positivo e bloqueia commit por
# engano. governanca/tests nem existe em projeto gerado pelo Copier
# (_exclude do copier.yml) -- so importa para o dev deste template.
NOMES_USADOS=$(
    {
        git grep -hoE 'process\.env\.[A-Za-z_][A-Za-z0-9_]*' -- . ':!*.md' ':!scripts/diff_docs.sh' ':!governanca/tests/*' 2>/dev/null | sed 's/^process\.env\.//'
        git grep -hoE 'os\.environ\["[A-Za-z_][A-Za-z0-9_]*' -- . ':!*.md' ':!scripts/diff_docs.sh' ':!governanca/tests/*' 2>/dev/null | sed 's/^os\.environ\["//'
        git grep -hoE "os\.environ\['[A-Za-z_][A-Za-z0-9_]*" -- . ':!*.md' ':!scripts/diff_docs.sh' ':!governanca/tests/*' 2>/dev/null | sed "s/^os\.environ\['//"
        git grep -hoE 'os\.environ\.get\("[A-Za-z_][A-Za-z0-9_]*' -- . ':!*.md' ':!scripts/diff_docs.sh' ':!governanca/tests/*' 2>/dev/null | sed 's/^os\.environ\.get("//'
        git grep -hoE "os\.environ\.get\('[A-Za-z_][A-Za-z0-9_]*" -- . ':!*.md' ':!scripts/diff_docs.sh' ':!governanca/tests/*' 2>/dev/null | sed "s/^os\.environ\.get('//"
        git grep -hoE 'os\.getenv\("[A-Za-z_][A-Za-z0-9_]*' -- . ':!*.md' ':!scripts/diff_docs.sh' ':!governanca/tests/*' 2>/dev/null | sed 's/^os\.getenv("//'
        git grep -hoE "os\.getenv\('[A-Za-z_][A-Za-z0-9_]*" -- . ':!*.md' ':!scripts/diff_docs.sh' ':!governanca/tests/*' 2>/dev/null | sed "s/^os\.getenv('//"
        git grep -hoE '\$env:[A-Za-z_][A-Za-z0-9_]*' -- . ':!*.md' ':!scripts/diff_docs.sh' ':!governanca/tests/*' 2>/dev/null | sed 's/^\$env://'
    } | sort -u
)

if [ ! -f .env.example ]; then
    echo "  .env.example nao existe -- checagem pulada."
elif [ -z "$NOMES_USADOS" ]; then
    echo "  Nenhuma referencia a variavel de ambiente encontrada no codigo."
else
    NOMES_DOC=$(grep -oE '^[A-Za-z_][A-Za-z0-9_]*=' .env.example | sed 's/=$//' | sort -u)
    FALTANDO=""
    for nome in $NOMES_USADOS; do
        if ! printf '%s\n' "$NOMES_DOC" | grep -qx "$nome"; then
            FALTANDO="$FALTANDO $nome"
        fi
    done
    if [ -n "$FALTANDO" ]; then
        echo "ERRO: variavel(is) de ambiente referenciada(s) no codigo mas ausente(s) de .env.example:${FALTANDO}"
        echo "  Corrija adicionando o NOME (sem valor) em .env.example, ou confirme"
        echo "  que e falso positivo (deteccao heuristica, ver docs/TROUBLESHOOTING.md)"
        echo "  antes de forcar o commit."
        exit 1
    fi
    echo "  Nenhuma variavel de ambiente sem registro em .env.example."
fi

exit 0
