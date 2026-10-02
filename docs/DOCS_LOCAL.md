# Documentos locais (`docs-local/`)

Pasta gitignored, na raiz do projeto, pra material de trabalho pessoal
que não é entregável do projeto nem documentação compartilhada — não
entra no repositório, não é lido por quem clona, não precisa de revisão
de ninguém. Existe pra não ficar "anotação solta" espalhada por aí nem
misturada com `docs/` (que é committed e compartilhado).

`docs-local/` inteira já está no `.gitignore` — pode criar quantas
subpastas quiser dentro dela sem precisar editar o `.gitignore` de
novo. Convenção inicial, duas subpastas:

```
docs-local/
├── estudo/
│   └── licoes-aprendidas.md      ← gerado pela skill `licoes-aprendidas`
└── apresentacao/
    ├── aula-<tema>.md            ← gerado pela skill `roteiro-de-aula`
    └── slides-<tema>.md          ← gerado pela skill `ideias-de-slides`
```

## Pra que serve cada subpasta

- **`estudo/`**: reflexão/aprendizado sobre o próprio projeto — o que
  deu errado, o que você aprendeu, em formato pra estudo ou
  retrospectiva. **Não é troubleshooting técnico** — isso já tem lugar
  certo em `docs/TROUBLESHOOTING.md` (causa raiz) e
  `docs/PADROES_DE_RISCO.md` (padrão estrutural). A skill
  `licoes-aprendidas` só reaproveita o que já está documentado ali (ou
  na conversa da sessão), traduzindo pra um formato de
  aprendizado/narrativa — nunca re-investiga nem inventa causa raiz
  nova.
- **`apresentacao/`**: material de storytelling pra apresentar o
  projeto — aula/disciplina da pós, atualização pra um chefe, defesa de
  TCC. Roteiro de fala (`aula-<tema>.md`) e ideias de slide com paleta
  de cores e texto por slide (`slides-<tema>.md`), pensados como
  **rascunho de preparação**, não como produto final — a montagem de
  verdade do deck (`.pptx` ou Artifact tipo Slides) é um passo
  separado e deliberado, depois que o conteúdo já estiver bom.

## Isso não é a mesma coisa que o Nível A (Acadêmico)

A skill `inicio-de-projeto` já classifica projetos até um nível **A
(Acadêmico)** — mas esse nível é sobre **reprodutibilidade** (seeds
fixas, ambiente travado, model card: "outra pessoa roda isso daqui a
dois anos e obtém o mesmo número"). `docs-local/apresentacao/` é sobre
**storytelling/comunicação** do resultado, eixo completamente
diferente. Um projeto pode precisar dos dois, de só um, ou de nenhum —
não confundir "projeto acadêmico" (nível, reprodutibilidade) com
"preciso apresentar isso" (`docs-local/`, comunicação).

## Skills que geram esse conteúdo

Skills pessoais (`~/.claude/skills/`, não fazem parte deste
repositório-template — disponíveis em qualquer projeto que você abrir):

- `licoes-aprendidas` → `docs-local/estudo/licoes-aprendidas.md`
- `roteiro-de-aula` → `docs-local/apresentacao/aula-<tema>.md`
- `ideias-de-slides` → `docs-local/apresentacao/slides-<tema>.md`

Também vale pra projeto de empresa, não só de estudo — ex.: resumo de
um incidente pra apresentar pro time, sem virar artefato permanente do
repositório.
