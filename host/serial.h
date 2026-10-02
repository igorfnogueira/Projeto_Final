#ifndef HOST_SERIAL_H
#define HOST_SERIAL_H

#include <stddef.h>

#define PULSO_SERVO_0_US 1000
#define PULSO_SERVO_90_US 1500

/* Linhas da janela, na ordem da classe. Retorna o pulso em us, ou 0 se o servo fica parado. */
int linhas_da_janela(int classe, char *destino, size_t n);

#endif
