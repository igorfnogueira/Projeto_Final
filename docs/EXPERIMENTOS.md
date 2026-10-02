# Experimentos

Uma linha por treino. Ainda não há run.

| Hipótese | Config | Métrica | Conclusão |
| --- | --- | --- | --- |
| CNN com max global separa as quatro classes | seed 42, 8 clipes por classe, 40 épocas | teste 0,75; `abrir_09` e `abrir_10` saíram fechar | Descartada. O max perde a ordem da frase |
| CNN com passo 3 e flatten | seed 42, 60 épocas | teste 0,875; `abrir_10` saiu fechar | Descartada |
| Centróide do MFCC | médias dos clipes 01–08, INT8, seed 42 | teste float 1,00 e INT8 1,00 em 8 clipes | Aceita neste dado. Uma voz só | --- |
