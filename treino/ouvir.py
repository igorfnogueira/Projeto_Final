"""Uma janela de 1 s do microfone do computador.

Usa o mesmo MFCC em C e o mesmo INT8 do firmware. Imprime a classe e,
em abrir ou fechar, a linha do servo. O servo do Wokwi não se move aqui.
"""

import ctypes
import subprocess
import sys

import numpy as np

from treino.mfcc import load_config
from treino.transcript import ROOT, _biblioteca, _contrato, _mfcc_c
from treino.train import _predict_int8

HOST = ROOT / "host"
SERIAL = HOST / "serial.dll"
AMOSTRAS = 16000
TAXA = 16000


def _serial():
    fonte = HOST / "serial.c"
    if not SERIAL.is_file() or SERIAL.stat().st_mtime < fonte.stat().st_mtime:
        subprocess.check_call(
            ["gcc", "-shared", "-O2", "-I", str(HOST), "-o", str(SERIAL), str(fonte)],
            cwd=ROOT,
        )
    lib = ctypes.CDLL(str(SERIAL))
    lib.linhas_da_janela.argtypes = [ctypes.c_int, ctypes.c_char_p, ctypes.c_size_t]
    lib.linhas_da_janela.restype = ctypes.c_int
    return lib


def texto_da_janela(pcm, lib_mfcc, lib_serial, modelo):
    coeficientes = _mfcc_c(lib_mfcc, pcm).astype(np.float32)
    pred, _, _, _ = _predict_int8(modelo, coeficientes[None, ...])
    destino = ctypes.create_string_buffer(64)
    lib_serial.linhas_da_janela(int(pred[0]), destino, len(destino))
    return destino.value.decode("ascii")


def gravar():
    import sounddevice as sd

    quadro = sd.rec(AMOSTRAS, samplerate=TAXA, channels=1, dtype="int16")
    sd.wait()
    return np.squeeze(quadro)


def salvar(pcm, caminho):
    import wave

    caminho.parent.mkdir(parents=True, exist_ok=True)
    with wave.open(str(caminho), "wb") as arquivo:
        arquivo.setnchannels(1)
        arquivo.setsampwidth(2)
        arquivo.setframerate(TAXA)
        arquivo.writeframes(np.ascontiguousarray(pcm, dtype="<i2").tobytes())


def reproduzir(pcm):
    import sounddevice as sd

    sd.play(np.ascontiguousarray(pcm, dtype=np.int16), samplerate=TAXA)
    sd.wait()


def main():
    config = load_config()
    _contrato(config)
    lib_mfcc = _biblioteca()
    lib_serial = _serial()
    modelo = (ROOT / "treino" / "saida" / "modelo.tflite").read_bytes()
    pasta = ROOT / "dataset" / ".cache" / "ouvir"
    print("Cada tomada grava 1 s e toca de volta. Ctrl+C encerra.", file=sys.stderr, flush=True)
    tomada = 0
    while True:
        tomada += 1
        print("Fale agora.", file=sys.stderr, flush=True)
        try:
            pcm = gravar()
        except KeyboardInterrupt:
            return
        except Exception as exc:
            raise SystemExit(f"não foi possível abrir o microfone: {exc}") from exc
        if getattr(pcm, "shape", None) != (AMOSTRAS,):
            raise SystemExit("a gravação não tem 1 s")
        caminho = pasta / f"tomada_{tomada:02d}.wav"
        salvar(pcm, caminho)
        print(f"Reproduzindo {caminho}", file=sys.stderr, flush=True)
        try:
            reproduzir(pcm)
        except KeyboardInterrupt:
            return
        except Exception as exc:
            print(f"não foi possível tocar: {exc}", file=sys.stderr)
        sys.stdout.write(texto_da_janela(pcm, lib_mfcc, lib_serial, modelo))
        sys.stdout.flush()


if __name__ == "__main__":
    main()
