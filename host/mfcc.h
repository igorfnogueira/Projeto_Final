#ifndef HOST_MFCC_H
#define HOST_MFCC_H

#include <stdint.h>

#define MFCC_AMOSTRAS 16000
#define MFCC_QUADROS 99
#define MFCC_COEF 13

/* Tensor 99×13, linha a linha, a partir de PCM 16-bit da janela congelada. */
void mfcc_janela(const int16_t *pcm, double *saida);

#endif
