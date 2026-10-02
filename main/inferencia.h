#ifndef MAIN_INFERENCIA_H
#define MAIN_INFERENCIA_H

#include <stdint.h>

#ifdef __cplusplus
extern "C" {
#endif

int inferencia_iniciar(void);
int classificar_pcm(const int16_t *pcm);

#ifdef __cplusplus
}
#endif

#endif
