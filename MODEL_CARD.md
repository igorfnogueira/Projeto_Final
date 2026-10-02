# Model card

Uso pretendido: classificar uma janela de 1 s em `silencio`, `desconhecido`, `abrir` ou `fechar`, e mover o servo só em `abrir` (90°) e `fechar` (0°). A frase da classe `abrir` é "abrir porta". A da classe `fechar` é "fechar porta".

O modelo é o centróide de cada classe no tensor MFCC 99×13. A saída é a média da distância quadrática, com sinal negativo. O arquivo é `treino/saida/modelo.tflite`, INT8, seed 42. No teste (clipes 09 e 10 de cada classe, 8 ao todo) a acurácia float e a INT8 foram 1,00. Uma CNN rasa, no mesmo corte, classificou "abrir porta" como fechar. A decisão está no ADR-0005.

Limitações: uma voz só, sala quieta, oito clipes por classe. Voz de outro integrante, ruído de apresentação e fala fora dessas quatro médias podem cair na classe errada. O firmware ainda não roda este arquivo. O MFCC em C ainda não foi comparado ao do notebook.
