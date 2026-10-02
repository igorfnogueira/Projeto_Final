"""Transcript da janela conhecida: MFCC em C e classe do INT8.

Imprime, nesta ordem:

    classe silencio
    classe desconhecido
    classe abrir
    classe fechar
    diferenca <maior absoluta>
"""

import ctypes
import subprocess
import sys
from pathlib import Path

import numpy as np

from treino.mfcc import load_config, read_pcm16_mono
from treino.train import LABELS, _predict_int8

ROOT = Path(__file__).resolve().parents[1]
HOST = ROOT / "host"
DLL = HOST / "mfcc.dll"
ORDEM = ("silencio", "desconhecido", "abrir", "fechar")
JANELAS = {
    "silencio": ROOT / "dataset" / "igor" / "silencio_09.wav",
    "desconhecido": ROOT / "dataset" / "desconhecido" / "desconhecido_09.wav",
    "abrir": ROOT / "dataset" / "igor" / "abrir_09.wav",
    "fechar": ROOT / "dataset" / "igor" / "fechar_09.wav",
}


def _contrato(config):
    audio = config["audio"]
    mfcc = config["mfcc"]
    esperado = {
        "amostras": audio["window_samples"] == 16000,
        "taxa": audio["sample_rate_hz"] == 16000,
        "pre": mfcc["preemphasis"] == 0.97,
        "quadro": mfcc["frame_length_samples"] == 320,
        "passo": mfcc["frame_step_samples"] == 160,
        "quadros": mfcc["n_frames"] == 99,
        "fft": mfcc["n_fft"] == 512,
        "mels": mfcc["n_mels"] == 40,
        "coef": mfcc["n_mfcc"] == 13,
        "fmin": mfcc["fmin_hz"] == 0,
        "fmax": mfcc["fmax_hz"] == 8000,
        "piso": mfcc["log_floor"] == 1e-10,
        "lifter": mfcc["lifter"] == 22,
        "janela": mfcc["window_fn"] == "hann",
        "mel": mfcc["mel_scale"] == "htk",
        "energia": mfcc["include_energy"] is False,
        "classes": config["labels"] == list(LABELS),
    }
    quebrados = [nome for nome, ok in esperado.items() if not ok]
    if quebrados:
        raise SystemExit("config congelado divergiu do MFCC em C: " + ", ".join(quebrados))


def _biblioteca():
    fonte = HOST / "mfcc.c"
    if not DLL.is_file() or DLL.stat().st_mtime < fonte.stat().st_mtime:
        subprocess.check_call(
            ["gcc", "-shared", "-O2", "-I", str(HOST), "-o", str(DLL), str(fonte), "-lm"],
            cwd=ROOT,
        )
    lib = ctypes.CDLL(str(DLL))
    lib.mfcc_janela.argtypes = [
        ctypes.POINTER(ctypes.c_int16),
        ctypes.POINTER(ctypes.c_double),
    ]
    lib.mfcc_janela.restype = None
    return lib


def _mfcc_c(lib, pcm):
    saida = np.zeros(99 * 13, dtype=np.float64)
    amostras = np.ascontiguousarray(pcm, dtype=np.int16)
    lib.mfcc_janela(
        amostras.ctypes.data_as(ctypes.POINTER(ctypes.c_int16)),
        saida.ctypes.data_as(ctypes.POINTER(ctypes.c_double)),
    )
    return saida.reshape(99, 13)


def main():
    config = load_config()
    _contrato(config)
    lib = _biblioteca()
    ouro = np.load(ROOT / "treino" / "saida" / "vetor_dourado.npz")
    por_caminho = {
        str(p).replace("\\", "/"): i for i, p in enumerate(ouro["paths"])
    }
    modelo = (ROOT / "treino" / "saida" / "modelo.tflite").read_bytes()

    tensores = []
    maior = 0.0
    for nome in ORDEM:
        pcm = read_pcm16_mono(JANELAS[nome], config)
        c = _mfcc_c(lib, pcm)
        relativo = JANELAS[nome].relative_to(ROOT).as_posix()
        ref = ouro["mfcc"][por_caminho[relativo]]
        maior = max(maior, float(np.max(np.abs(c - ref))))
        tensores.append(c.astype(np.float32))

    pred, _, _, _ = _predict_int8(modelo, np.stack(tensores))
    falhou = False
    for nome, classe in zip(ORDEM, pred):
        rotulo = LABELS[int(classe)]
        print(f"classe {rotulo}")
        if rotulo != nome:
            falhou = True
            print(f"esperava {nome}, saiu {rotulo}", file=sys.stderr)
    print(f"diferenca {maior:.8e}")
    if falhou:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
