# Projeto_Final — contexto para IA

**Nível:** A (acadêmico). Ver `docs/NIVEL.md`.
**Stack:** ESP-IDF (C, esp32s3), notebook próprio (MFCC, TFLite INT8), `esp-tflite-micro`.
**Rodar:** `idf.py build`, depois simular o `diagram.json` no Wokwi.
**Testar:** no serial do Wokwi, a linha `servo 0` e depois `servo 90`.
**Lint:** não há comando de lint neste passo.

## Estrutura

Firmware em `main/`. O notebook ainda não existe. Decisões em `docs/adr/`. Plano em `PLANO.md`.

## Pontos únicos de mudança

O contrato de áudio futuro passa por um único config de MFCC, ainda não criado. O servo desta demo usa o GPIO 4.

## Convenções

- Commits: Conventional Commits (`feat:`, `fix:`, `docs:`, `chore:`)
- Decisões entre alternativas viram ADR em `docs/adr/` na hora da decisão
- Segredos nunca no código; nomes de variáveis em `.env.example`

## Governança de documentação

Use a skill `governanca-docs` ao fechar uma sessão que mudou comportamento, arquitetura, superfície de dados ou segurança.
Use a skill `auditoria-projeto` quando for pedida revisão periódica.

## Escopo

Ideias novas vão para `docs/ESTACIONAMENTO.md`, não para o código da tarefa atual.

## Notas do terminal

N2 → Sonnet | N3 → Opus, sempre em Plan Mode.

## Agent skills

### Issue tracker

Issues e specs deste repositório vivem no GitHub Issues. Veja `docs/agents/issue-tracker.md`.

### Triage labels

Cinco rótulos padrão, com o mesmo nome do papel: `needs-triage`, `needs-info`, `ready-for-agent`, `ready-for-human`, `wontfix`. Veja `docs/agents/triage-labels.md`.

### Domain docs

Single-context: `CONTEXT.md` na raiz e `docs/adr/`. Veja `docs/agents/domain.md`.
