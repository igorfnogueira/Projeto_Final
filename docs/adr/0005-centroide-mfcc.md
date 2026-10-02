# ADR-0005 — Centróide no tensor MFCC

Status: Aceito · Data: 2026-10-02

## Contexto

O tensor congelado é 99×13. O primeiro treino tem 8 clipes por classe. O modelo tem de caber na flash e na SRAM interna do ESP32-S3. A frase "abrir porta" não pode ser classificada como fechar.

## Decisão

Cada classe é a média dos MFCC de treino. A saída é a média da distância quadrática, com sinal negativo, até essas quatro médias. A classe é o argmax. A ordem é a do `mfcc_config.json`: silencio, desconhecido, abrir, fechar.

## Alternativas descartadas

- CNN rasa com max global — no teste, os dois clipes novos de "abrir porta" saíram como fechar. O max global perde a ordem da frase.
- CNN com convolução em passo 3 e flatten — acertou 7 de 8 e ainda trocou `abrir_10.wav` por fechar.
- MLP sobre os 1287 valores achatados — a primeira camada fica grande para oito clipes e para a SRAM, e não separou melhor do que a média da classe.

## Consequências

O INT8 sai de `treino/train.py` com seed 42. As médias usam só os clipes 01 a 08. Trocar a rede invalida o vetor dourado e o firmware que ainda vai embutir o `.tflite`.
