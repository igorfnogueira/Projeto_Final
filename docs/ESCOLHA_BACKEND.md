# Escolha de backend — qual usar pra qual tipo de projeto

Guia de decisão rápido, não exaustivo. Objetivo: escolher a ferramenta
pelo tamanho real do problema — trabalhando sozinho, o recurso mais
escasso é tempo de manutenção, não capacidade técnica da ferramenta.

## Tabela de decisão

| Situação | Escolha | Por quê |
|---|---|---|
| Ferramenta interna pequena, dashboard, cadastro simples, MVP pra validar ideia | **PocketBase** | Backend inteiro (banco + auth + storage + API) num binário único, um comando, deploy em VPS barato. Menor operação possível — sem stack de múltiplos serviços pra sustentar sozinho. Limite real: escrita single-writer (SQLite por baixo), não é pra escala grande. |
| Dado relacional real, relatório/consulta complexa, projeto que vai crescer, ou já usa Postgres em algum lugar | **Supabase** | Postgres de verdade — consulta relacional complexa, RLS (Row Level Security) pra controle fino por linha, `pgvector` se precisar de embedding/IA. Exige disciplina: **RLS obrigatório em toda tabela** (ver `docs/CHECKLIST_LANCAMENTO.md`), senão a `anon key` exposta no frontend dá acesso livre ao banco. |
| Quer self-host completo (não depender de SaaS de terceiro), mas precisa de mais do que PocketBase oferece (functions, storage, hosting integrado) | **Appwrite** | Meio-termo — roda em Docker (mais peso de operação que PocketBase, menos que manter um Supabase self-hosted), open-source, mais "com pilhas incluídas". |
| App com necessidade forte de tempo real/reatividade, stack TypeScript-first | **Convex** | Elimina categoria inteira de código de sincronização de estado que PocketBase/Supabase exigiriam escrever na mão — mas é mais opinativo, vale só se o projeto realmente precisa de reatividade como núcleo, não só "seria legal ter". |

## Regra prática

Comece pela linha de cima que descrever o projeto — não pule direto
pro Supabase "porque é o que eu já conheço" se o projeto real é do
tamanho de um PocketBase. Trocar de ferramenta depois que o projeto já
tem dado real e usuário é retrabalho; escolher pequeno demais pra um
projeto que vai crescer também é — o objetivo aqui é acertar o
tamanho, não a ferramenta mais familiar por padrão.

Se meio do caminho ficar claro que o projeto cresceu além da escolha
inicial (ex.: começou como ferramenta interna em PocketBase e virou
produto com múltiplos clientes), isso é decisão de arquitetura — vale
um ADR em `docs/adr/` registrando a migração e o motivo, não só trocar
silenciosamente.
