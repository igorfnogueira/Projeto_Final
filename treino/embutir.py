"""Gera o PCM das quatro janelas e o INT8 que o firmware lê da flash.

Os números saem de mfcc_config.json. Rode de novo se o config mudar.
"""

from pathlib import Path

from treino.mfcc import load_config, read_pcm16_mono

ROOT = Path(__file__).resolve().parents[1]
MODELO = ROOT / "treino" / "saida" / "modelo.tflite"
CABECALHO = ROOT / "main" / "embutidos.h"
CORPO = ROOT / "main" / "embutidos.c"
ROTULOS = ROOT / "host" / "rotulos.h"


def caminho_da_janela(rotulo):
    if rotulo == "desconhecido":
        return ROOT / "dataset" / "desconhecido" / "desconhecido_09.wav"
    return ROOT / "dataset" / "igor" / f"{rotulo}_09.wav"


def bloco(numeros, formato):
    linhas = []
    for i in range(0, len(numeros), 16):
        linhas.append("    " + ", ".join(formato(n) for n in numeros[i : i + 16]) + ",")
    return "\n".join(linhas)


def main():
    config = load_config()
    rotulos = list(config["labels"])
    amostras_n = int(config["audio"]["window_samples"])
    janelas = [read_pcm16_mono(caminho_da_janela(nome), config).tolist() for nome in rotulos]
    modelo = MODELO.read_bytes()
    nomes = ", ".join(f'"{nome}"' for nome in rotulos)

    ROTULOS.write_text(
        "\n".join(
            [
                "/* Gerado por python -m treino.embutir, a partir de mfcc_config.json. */",
                "#ifndef HOST_ROTULOS_H",
                "#define HOST_ROTULOS_H",
                "",
                f"#define ROTULO_N {len(rotulos)}",
                f"static const char *const ROTULOS[ROTULO_N] = {{{nomes}}};",
                "",
                "#endif",
                "",
            ]
        ),
        encoding="utf-8",
        newline="\n",
    )
    CABECALHO.write_text(
        "\n".join(
            [
                "/* Gerado por python -m treino.embutir, a partir de mfcc_config.json. */",
                "#ifndef MAIN_EMBUTIDOS_H",
                "#define MAIN_EMBUTIDOS_H",
                "",
                "#include <stdint.h>",
                "",
                f"#define JANELA_AMOSTRAS {amostras_n}",
                f"#define JANELA_N {len(rotulos)}",
                "",
                "extern const int16_t janela_pcm[JANELA_N][JANELA_AMOSTRAS];",
                "extern const unsigned char modelo_tflite[];",
                "extern const unsigned int modelo_tflite_len;",
                "",
                "#endif",
                "",
            ]
        ),
        encoding="utf-8",
        newline="\n",
    )
    texto = [
        "/* Gerado por python -m treino.embutir. Quatro janelas 09 e o INT8. */",
        '#include "embutidos.h"',
        "",
        "const int16_t janela_pcm[JANELA_N][JANELA_AMOSTRAS] = {",
    ]
    for amostras in janelas:
        texto.append("    {")
        texto.append(bloco(amostras, str))
        texto.append("    },")
    texto.append("};")
    texto.append("")
    texto.append("__attribute__((aligned(16))) const unsigned char modelo_tflite[] = {")
    texto.append(bloco(list(modelo), lambda n: f"0x{n:02x}"))
    texto.append("};")
    texto.append("const unsigned int modelo_tflite_len = sizeof(modelo_tflite);")
    texto.append("")
    CORPO.write_text("\n".join(texto), encoding="utf-8", newline="\n")


if __name__ == "__main__":
    main()
