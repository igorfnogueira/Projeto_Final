# Projeto_Final

Comandos ABRIR/FECHAR em português no ESP32-S3. Treino próprio no notebook (MFCC, TFLite INT8) e inferência com `esp-tflite-micro`. O Wokwi, neste passo, sobe o serial e move o servo. O primeiro INT8 está em `treino/saida/modelo.tflite` e o firmware roda esse arquivo nas quatro janelas conhecidas.

**Alvo:** `esp32s3`. **Nível:** A (acadêmico), ver `docs/NIVEL.md`.

## Stack

ESP-IDF em C, notebook próprio (MFCC e TFLite INT8) e o runtime `esp-tflite-micro`. A decisão e as alternativas descartadas estão em `docs/adr/0001-stack-inicial.md`.

## O que já está fechado

- A entrada no dispositivo é PCM. O MFCC roda em C com o `mfcc_config.json` já congelado: 16 kHz, janela de 1 s, quadro de 20 ms, passo de 10 ms, FFT 512, 13 coeficientes, tensor 99×13.
- Voz de quem não está no grupo cai em `desconhecido` e não move o servo. Não se guarda essa voz com identidade.
- O config congela com um WAV de 1 s. Depois, cada integrante grava 10 ABRIR, 10 FECHAR e 10 silêncio.
- A V1 fecha no Wokwi: o mesmo MFCC no notebook e em C, a mesma classe no serial, ABRIR a 90° e FECHAR a 0°. Silêncio e desconhecido ficam parados. O INMP441 vem depois disso.

## Build e simulador

```text
idf.py set-target esp32s3
idf.py build
```

Abra o `diagram.json` no Wokwi e inicie a simulação de novo depois do build, para carregar o firmware novo. O servo começa em 0°, sem linha de servo. O serial imprime, nesta ordem:

```text
classe silencio
classe desconhecido
classe abrir
servo 90
classe fechar
servo 0
```

Silêncio e desconhecido não movem o servo. Abrir vai a 90° e fechar volta a 0°. Cada janela permanece 1,5 s e o servo termina em 0°. Não há microfone no diagrama. O sinal do servo é o GPIO 4 (LEDC 50 Hz, 1000 µs em 0° e 1500 µs em 90°).

O treino é `python -m treino.train`, com a seed 42. O notebook `treino/treino.ipynb` chama o mesmo comando. O primeiro conjunto é só `dataset/igor/` mais `dataset/desconhecido/`. Os clipes 01 a 08 treinam; 09 e 10 ficam de fora.

Para ouvir uma frase no microfone do computador, sem o ESP32: `python -m treino.ouvir`. Cada tomada grava 1 s, toca essa gravação de volta e imprime a classe e a linha do servo. O WAV fica em `dataset/.cache/ouvir/`. O servo do Wokwi não se move nesse caminho. Ctrl+C encerra.

Dependências Python: `requirements.txt`, com o ambiente travado em `requirements.lock`.

## O que só o grupo grava

### Um clipe para congelar o config

Sala quieta, a frase "abrir porta". A frase inteira tem de caber em 1 s.

1. Instale o Audacity.
2. No canto inferior esquerdo, ponha a taxa do projeto em 16000 Hz.
3. Grave uma faixa. Se nascer em estéreo, use Faixas → Mix → Mix Stereo down to Mono.
4. Selecione exatamente 1,0 s de fala, com a frase inteira dentro da seleção.
5. Arquivo → Exportar → Exportar como WAV, codificação Signed 16-bit PCM.
6. Salve como `dataset/congelar/amostra.wav`.

### Dataset, depois do config congelado

Cada integrante, 16 kHz, mono, WAV 16-bit, 1 s:

1. 10 clipes de "abrir porta": `dataset/<nome>/abrir_01.wav` … `abrir_10.wav`.
2. 10 clipes de "fechar porta": `fechar_01.wav` … `fechar_10.wav`.
3. 10 clipes de silêncio na mesma sala: `silencio_01.wav` … `silencio_10.wav`.
4. Não grave outras pessoas.

### Placa real

Só depois da V1 no Wokwi. Não ligue o INMP441 antes disso. O sinal do servo e os pinos SCK, WS e SD ficam fora dos pinos de strap 0, 3, 45 e 46. A alimentação do servo é separada da lógica 3,3 V.
