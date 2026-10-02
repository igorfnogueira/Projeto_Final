# ADR-0001 — Stack inicial

Status: Aceito · Data: 2026-10-02

## Contexto

O trabalho pede comandos ABRIR/FECHAR em português no ESP32-S3, com treino, compressão e inferência no dispositivo, e a arguição pergunta janela, MFCC, formato do tensor e quantização INT8.

## Decisão

ESP-IDF em C no `esp32s3`, treino próprio no notebook (MFCC, modelo pequeno, TFLite INT8) e runtime `esp-tflite-micro`.

## Alternativas descartadas

- Edge Impulse — o treino e o INT8 ficam prontos, mas o grupo perde um lugar legível para explicar janela, MFCC, tensor e quantização.
- ESP-SR MultiNet — maduro, e o comando reconhecido é só chinês e inglês.

## Consequências

O MFCC em C tem de repetir o config do notebook. O runtime oficial entra só no passo da inferência. Este passo ainda não carrega modelo.
