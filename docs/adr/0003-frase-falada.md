# ADR-0003 — Frase falada

Status: Substituído por ADR-0004 · Data: 2026-10-02

## Contexto

A janela é de 1 s. A classe que abre a porta precisa de uma frase estável, senão os dez clipes por pessoa ensinam dois comandos diferentes.

## Decisão

A classe `abrir` é a frase "abrir a porta". A classe `fechar` é "fechar a porta". Os nomes das classes e dos arquivos não mudam.

## Alternativas descartadas

- Só "abrir" e "fechar" — qualquer "abrir" dispararia a porta.
- "abrir porta", sem o artigo — menos natural, e misturar as duas frases nos mesmos dez clipes divide o dado.

## Consequências

A frase inteira tem de caber em 1 s, sem corte e sem alongar o áudio. Se não couber, grava-se de novo, mais curto.
