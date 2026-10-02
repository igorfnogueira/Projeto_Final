# Checklist antes de lançar (pré-produção)

Lista curta, pra rodar sozinho em poucas horas antes de colocar algo
novo no ar — não substitui revisão de segurança formal em projeto
grande, mas cobre os erros mais comuns de projeto construído com
ajuda de IA sem time de dev por trás.

## Banco de dados

- [ ] **RLS (Row Level Security) habilitado em TODA tabela exposta**
  (Supabase/Postgres). Tabela criada por migration, SQL direto ou
  agente de IA **não vem com RLS ligado por padrão** — checar uma por
  uma, sem exceção pra "tabela de lookup" ou "é só um protótipo".
- [ ] Cada tabela com RLS tem **policy** para cada operação que ela
  realmente usa (select/insert/update/delete) — lembrar que grant sem
  policy libera tudo (falha aberto), policy sem grant bloqueia tudo
  (falha fechado); os dois precisam estar certos juntos.
- [ ] `service_role` (ou equivalente com bypass de RLS) **nunca**
  aparece em código que roda no navegador/cliente — só em backend/
  função server-side.

## Segredo e credencial

- [ ] `grep -r "service_role\|SUPABASE_SERVICE\|sb_secret_" ./public ./dist ./build`
  (ou pasta equivalente de build do seu framework) antes de fazer
  deploy — confirma que nenhuma chave sensível foi parar em JS servido
  pro navegador.
- [ ] Nenhuma chave de API, token ou senha commitada no histórico do
  git (`git log -p | grep -i "key\|secret\|token"` numa amostra, ou
  ferramenta de scan tipo gitleaks).
- [ ] `.env`/`.env.local`/`.envrc` reais estão no `.gitignore` — e
  **já estavam** desde o primeiro commit do repo (não adianta
  adicionar depois se já foi commitado uma vez).

## Autenticação e acesso

- [ ] Rotas/endpoints administrativos ou sensíveis exigem autenticação
  real (não só "esconder o link").
- [ ] HTTPS ativo (a maioria dos hosts gerenciados já vem assim por
  padrão — confirmar, não assumir).

## Se esta entrega é acadêmica (TCC, disciplina, avaliador externo)

Motivo é funcional, não de sigilo: `.githooks/pre-commit` exige o CLI
`claude` autenticado e rede disponível — sem isso, **trava** quem for
clonar/avaliar o projeto, mesmo que a pessoa nunca vá dar `git commit`.

- [ ] Removi `.githooks/` (pre-commit, commit-msg) do que será
  entregue — eram enforcement local, não fazem parte do produto.
- [ ] Removi `setup.ps1` — só existia pra ativar `.githooks/`, fica sem
  função sem ele.
- [ ] Deixei `docs/`, ADRs e o workflow de CI (gitleaks) como estão —
  não dependem de CLI autenticado, não bloqueiam quem for avaliar, e
  ainda sinalizam cuidado técnico.

## Antes de considerar concluído

- [ ] Rodei este checklist com um `.env`/credencial **fictícia**, não
  a de produção, se precisei testar algum passo manualmente.
- [ ] Se algo aqui falhou e exigiu mais de uma tentativa pra entender
  a causa raiz, virou entrada em `docs/TROUBLESHOOTING.md` — não fica
  só resolvido "de cabeça".
- [ ] **Se este é um projeto acadêmico**, rodei a seção acima antes de
  entregar — fácil esquecer porque nada no fluxo normal de commit avisa
  sobre isso.

Ver também: `SECURITY.md` (mecanismo da trava de segredo deste
template) e `docs/ESCOLHA_BACKEND.md` (RLS é obrigatório especialmente
se você escolheu Supabase/Postgres — outros backends têm modelo de
permissão diferente, mas a exigência de "toda tabela tem controle de
acesso revisado" vale igual).
