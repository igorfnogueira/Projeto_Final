#include "serial.h"

#include <stdio.h>
#include <string.h>

#include "rotulos.h"

int linhas_da_janela(int classe, char *destino, size_t n)
{
    const char *nome;
    int pulso = 0;
    int escrito;

    if (classe < 0 || classe >= ROTULO_N) {
        if (n > 0) {
            destino[0] = '\0';
        }
        return 0;
    }
    nome = ROTULOS[classe];

    if (strcmp(nome, "abrir") == 0) {
        escrito = snprintf(destino, n, "classe %s\nservo 90\n", nome);
        pulso = PULSO_SERVO_90_US;
    } else if (strcmp(nome, "fechar") == 0) {
        escrito = snprintf(destino, n, "classe %s\nservo 0\n", nome);
        pulso = PULSO_SERVO_0_US;
    } else {
        escrito = snprintf(destino, n, "classe %s\n", nome);
    }

    if (escrito < 0 || (size_t)escrito >= n) {
        if (n > 0) {
            destino[0] = '\0';
        }
        return 0;
    }
    return pulso;
}
