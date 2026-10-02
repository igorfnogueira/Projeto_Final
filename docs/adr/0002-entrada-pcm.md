# ADR-0002 — Entrada PCM com MFCC no dispositivo

Status: Aceito · Data: 2026-10-02

## Contexto

O classificador não lê o áudio cru. Ele lê um tensor MFCC de uma janela de 1 s. A disciplina pede o caminho da leitura até a inferência no dispositivo, e a placa com INMP441 vai entregar PCM.

## Decisão

A entrada no firmware é sempre PCM. O MFCC roda no dispositivo, em C, com o mesmo config do notebook.

## Alternativas descartadas

- Tensor MFCC já calculado no notebook e embutido no firmware — prova o interpretador e deixa o extrator para depois. O vetor dourado não cobriria a etapa que a placa precisa.

## Consequências

O vetor dourado compara o MFCC do notebook, o MFCC em C e a classe no serial. Um coeficiente diferente entre Python e C quebra a classe no chip.
