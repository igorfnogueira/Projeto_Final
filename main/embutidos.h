/* Gerado por python -m treino.embutir, a partir de mfcc_config.json. */
#ifndef MAIN_EMBUTIDOS_H
#define MAIN_EMBUTIDOS_H

#include <stdint.h>

#define JANELA_AMOSTRAS 16000
#define JANELA_N 4

extern const int16_t janela_pcm[JANELA_N][JANELA_AMOSTRAS];
extern const unsigned char modelo_tflite[];
extern const unsigned int modelo_tflite_len;

#endif
