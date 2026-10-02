#!/usr/bin/env python3
"""
Trava de segredos para agentes (Claude Code e Cursor).

Transforma a regra "acesso a .env de producao ou service_role exige
confirmacao" em bloqueio/pergunta automatica. Uma unica logica; o
argumento --adapter so muda o formato da resposta.

  --adapter claude   hook PreToolUse do Claude Code  (JSON em stdout, exit 0)
  --adapter cursor   hooks beforeReadFile / beforeShellExecution /
                     beforeTabFileRead do Cursor     (JSON em stdout;
                     falha => exit 2 = bloqueia)

Limite honesto: isto le o TEXTO do comando. Nao enxerga o que um script
faz por dentro (ex.: `python import_resultados.py` carrega o .env sozinho).
Por isso a regra do importador sem --dry-run existe abaixo, e por isso a
camada real de protecao e nao deixar a service_role de producao como
credencial padrao de tarefas de agente.

Seguranca do proprio hook:
  - nunca imprime, loga nem repete o comando, o conteudo de arquivo ou
    qualquer valor de chave; as mensagens sao textos fixos;
  - o campo `content` que o Cursor entrega em beforeReadFile (conteudo do
    .env!) e descartado logo apos o parse, sem ser lido;
  - qualquer excecao interna falha FECHADO: Claude => ask, Cursor => deny.
"""

import json
import re
import sys

# --- arquivos .env "reais" -------------------------------------------------
# Seguros (podem ser lidos): .env.example / .env.sample / .env.template
SUFIXOS_SEGUROS = {"example", "sample", "template"}

# Em texto de comando: .env, .env.local, .env.production, prod.env, .envrc ...
# .envrc entra explicitamente (mesmo tratamento do lado do caminho); o
# lookahead genérico continua impedindo casar `.environ` (nao e segredo).
ENV_EM_COMANDO = re.compile(
    r"\.env(?:rc(?![A-Za-z0-9_])|(?:\.[A-Za-z0-9_.-]+)?(?![A-Za-z0-9_]))"
)

# Credenciais / carregamento de credencial citados no comando.
SEGREDO_EM_COMANDO = re.compile(
    r"SERVICE_ROLE|service_role|sb_secret_|SUPABASE_SERVICE|"
    r"dotenv_values|load_dotenv|create_client\s*\(",
    re.IGNORECASE,
)

# Importador que grava no banco real (regra do CLAUDE.md do hub).
IMPORTADOR = re.compile(r"import_(?:resultados|mapeamento)\.py")

MSG_LEITURA = (
    "Bloqueado pela trava de segredos: leitura de arquivo .env real. "
    "Use .env.example ou peca ao dono para rodar no terminal dele."
)
MSG_SHELL = (
    "Confirmacao exigida: o comando referencia .env real, service_role ou "
    "credencial de producao. Confirme com o dono antes de rodar."
)
MSG_IMPORTADOR = (
    "Confirmacao exigida: importador sem --dry-run grava no banco real "
    "(regra do CLAUDE.md). Confirme com o dono antes de rodar."
)
MSG_FALHA = "Trava de segredos falhou ao avaliar a chamada; falhando fechado."


def caminho_env_real(caminho) -> bool:
    """True se o caminho/glob aponta para um .env real (nao example)."""
    if not isinstance(caminho, str) or not caminho:
        return False
    base = caminho.replace("\\", "/").rstrip("/").rsplit("/", 1)[-1].lower()
    if base == ".env":
        return True
    if base.startswith(".env"):
        ultimo = base.rsplit(".", 1)[-1]
        return ultimo not in SUFIXOS_SEGUROS
    if base.endswith(".env") and len(base) > 4:  # prod.env, dev.env
        return True
    return False


def comando_cita_env_real(comando: str) -> bool:
    for m in ENV_EM_COMANDO.finditer(comando):
        if m.group(0).lower().rsplit(".", 1)[-1] not in SUFIXOS_SEGUROS:
            return True
    return False


# Excecao estreita: "vercel env pull" grava o segredo direto da API
# autenticada do Vercel pro disco, sem NUNCA passar pelo contexto do
# agente (ao contrario de `cat .env`, que devolveria o valor pra mim).
# So libera se o comando inteiro for exatamente essa chamada, sem
# encadeamento (;, &&, ||, |, backtick, $(...)) — encadeamento invalida
# o atalho e cai na regra normal, pra ninguem contrabandear outra coisa
# junto ("vercel env pull; cat .env" nao passa aqui).
#
# ACHADO (revisor-cetico, pre-commit, 2026-09-22): a versao anterior
# usava \S+ nos valores de --environment= e --git-branch=, que aceita
# QUALQUER token sem espaco -- inclusive `<(cat${IFS}.env>/dev/stderr)`
# (process substitution, sem espaco) e `${SUPABASE_SECRET_KEY}`
# (expansao de variavel). ENCADEAMENTO_SHELL nao cobria `<`, `>`, `${`,
# entao os dois passavam como "confiavel" e liberavam sem ask. Corrigido
# trocando \S+ por allowlist fechada de charset (sem <>(){}$`;&|),
# nunca denylist -- denylist sempre corre risco de faltar um caractere.
VERCEL_ENV_PULL = re.compile(
    r"^\s*vercel\s+env\s+pull"
    r"(?:\s+--environment=[A-Za-z0-9_-]+"
    r"|\s+--yes"
    r"|\s+--git-branch=[A-Za-z0-9._/-]+"
    r"|\s+\.env(?:\.[A-Za-z0-9_.-]+)?)*"
    r"\s*$",
    re.IGNORECASE,
)
ENCADEAMENTO_SHELL = re.compile(r"[;&|`<>(){}$]")


def comando_vercel_env_pull_confiavel(comando: str) -> bool:
    if ENCADEAMENTO_SHELL.search(comando):
        return False
    return bool(VERCEL_ENV_PULL.match(comando))


def avalia_comando(comando):
    """Retorna (decisao, motivo) para um comando de shell, ou (None, None)."""
    if not isinstance(comando, str) or not comando:
        return None, None
    if comando_vercel_env_pull_confiavel(comando):
        return None, None
    if comando_cita_env_real(comando) or SEGREDO_EM_COMANDO.search(comando):
        return "ask", MSG_SHELL
    if IMPORTADOR.search(comando) and "--dry-run" not in comando:
        return "ask", MSG_IMPORTADOR
    return None, None


def avalia_caminhos(valores):
    for v in valores:
        itens = v if isinstance(v, (list, tuple)) else [v]
        for item in itens:
            if caminho_env_real(item):
                return "deny", MSG_LEITURA
    return None, None


def decide(adapter: str, data: dict):
    """Nucleo puro (testavel). Retorna (decisao, motivo); decisao em
    {None, 'ask', 'deny'}."""
    if adapter == "claude":
        nome = data.get("tool_name") or ""
        entrada = data.get("tool_input") or {}
        if nome in ("Bash", "PowerShell"):
            return avalia_comando(entrada.get("command"))
        if nome in ("Read", "Edit", "Write", "NotebookEdit"):
            return avalia_caminhos([entrada.get("file_path"), entrada.get("notebook_path")])
        if nome == "Grep":
            # `pattern` de Grep e o texto buscado, nao um alvo: fica de fora.
            return avalia_caminhos([entrada.get("path"), entrada.get("paths"), entrada.get("glob")])
        if nome == "Glob":
            return avalia_caminhos([entrada.get("pattern"), entrada.get("path")])
        return None, None

    # cursor: o evento se reconhece pelo formato do stdin
    entrada = data.get("tool_input") if isinstance(data.get("tool_input"), dict) else {}
    comando = data.get("command") or entrada.get("command")
    if isinstance(comando, str):
        return avalia_comando(comando)
    return avalia_caminhos([data.get("file_path"), data.get("path"), entrada.get("file_path")])


def responde(adapter: str, decisao, motivo) -> int:
    if adapter == "claude":
        if decisao is not None:
            print(json.dumps({"hookSpecificOutput": {
                "hookEventName": "PreToolUse",
                "permissionDecision": decisao,
                "permissionDecisionReason": motivo,
            }}))
        return 0
    # cursor
    if decisao is None:
        print(json.dumps({"permission": "allow"}))
        return 0
    print(json.dumps({"permission": decisao, "user_message": motivo, "agent_message": motivo}))
    return 2 if decisao == "deny" else 0


def main(argv) -> int:
    adapter = "claude"
    if "--adapter" in argv:
        i = argv.index("--adapter")
        if i + 1 < len(argv):
            adapter = argv[i + 1]
    if adapter not in ("claude", "cursor"):
        adapter = "claude"
    try:
        bruto = sys.stdin.buffer.read().decode("utf-8-sig", errors="replace")  # Cursor envia BOM no stdin
        data = json.loads(bruto)
        del bruto
        if not isinstance(data, dict):
            raise ValueError("stdin nao e objeto JSON")
        data.pop("content", None)  # conteudo do arquivo (pode ser o proprio .env)
        decisao, motivo = decide(adapter, data)
        return responde(adapter, decisao, motivo)
    except Exception:  # noqa: BLE001 — falha fechada, sem vazar detalhe
        if adapter == "claude":
            return responde("claude", "ask", MSG_FALHA)
        sys.stderr.write(MSG_FALHA + "\n")
        print(json.dumps({"permission": "deny", "user_message": MSG_FALHA, "agent_message": MSG_FALHA}))
        return 2


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
