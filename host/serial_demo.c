#include "rotulos.h"
#include "serial.h"

#include <stdio.h>

/* As classes, na ordem do config: silencio, desconhecido, abrir, fechar. */
int main(void)
{
    int classe;

    for (classe = 0; classe < ROTULO_N; classe++) {
        char texto[64];
        linhas_da_janela(classe, texto, sizeof(texto));
        fputs(texto, stdout);
    }
    return 0;
}
