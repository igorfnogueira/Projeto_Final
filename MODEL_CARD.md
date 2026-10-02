# Model card

Uso pretendido: classificar uma janela de 1 s em `silencio`, `desconhecido`, `abrir` ou `fechar`, e mover o servo só em `abrir` (90°) e `fechar` (0°).

O modelo ainda não foi treinado. <!-- PENDENTE: métricas do primeiro INT8 -->

Limitações já conhecidas: o áudio de treino será só dos integrantes, em sala quieta. Voz de fora, ruído de apresentação e silêncio não devem mover o servo. A quantização será INT8 com dataset representativo, ainda não coletado.
