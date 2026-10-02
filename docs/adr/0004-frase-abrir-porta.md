# ADR-0004 — Frase falada "abrir porta"

Status: Aceito · Data: 2026-10-02

Substitui ADR-0003.

## Contexto

O clipe que congela o config, `dataset/congelar/amostra.wav`, foi gravado com a frase "abrir porta". A janela continua de 1 s.

## Decisão

A classe `abrir` é a frase "abrir porta". A classe `fechar` é "fechar porta". Os nomes das classes e dos arquivos não mudam.

## Alternativas descartadas

- "abrir a porta" e "fechar a porta" — era o texto do ADR-0003. O áudio já gravado não usa o artigo. Misturar as duas formas nos dez clipes divide o dado.
- Só "abrir" e "fechar" — qualquer "abrir" dispararia a porta.

## Consequências

Todo clipe de treino e o da placa repetem essa frase, inteira, dentro de 1 s. O artigo não entra.
