"""MFCC do contrato congelado em mfcc_config.json.

A conta é a referência do vetor dourado. O firmware em C tem de chegar
no mesmo tensor, com o mesmo config, sem outra biblioteca no meio.
"""

import json
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
CONFIG_PATH = ROOT / "mfcc_config.json"


def load_config(path=CONFIG_PATH):
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def read_pcm16_mono(path, config):
    """Lê um WAV PCM 16-bit mono na taxa do config e devolve int16."""
    import struct

    rate = config["audio"]["sample_rate_hz"]
    window = config["audio"]["window_samples"]
    with open(path, "rb") as f:
        riff, _, wave = struct.unpack("<4sI4s", f.read(12))
        if riff != b"RIFF" or wave != b"WAVE":
            raise ValueError(f"não é WAV: {path}")
        samples = None
        fmt = None
        while True:
            hdr = f.read(8)
            if len(hdr) < 8:
                break
            cid, csize = struct.unpack("<4sI", hdr)
            start = f.tell()
            if cid == b"fmt ":
                fmt = struct.unpack("<HHIIHH", f.read(16))
            elif cid == b"data":
                raw = f.read(csize)
                samples = np.frombuffer(raw, dtype="<i2").copy()
            f.seek(start + csize + (csize % 2))
    if fmt is None or samples is None:
        raise ValueError(f"WAV incompleto: {path}")
    audio_format, channels, file_rate, _, block_align, bits = fmt
    if (audio_format, channels, file_rate, bits, block_align) != (1, 1, rate, 16, 2):
        raise ValueError(
            f"formato de {path}: fmt={audio_format} ch={channels} {file_rate}Hz {bits}bit"
        )
    if samples.shape[0] != window:
        raise ValueError(f"{path} tem {samples.shape[0]} amostras, o contrato pede {window}")
    return samples


def _hz_to_mel(hz):
    return 2595.0 * np.log10(1.0 + hz / 700.0)


def _mel_to_hz(mel):
    return 700.0 * (10.0 ** (mel / 2595.0) - 1.0)


def _mel_filterbank(config):
    mfcc = config["mfcc"]
    sr = config["audio"]["sample_rate_hz"]
    n_fft = mfcc["n_fft"]
    n_mels = mfcc["n_mels"]
    n_freq = n_fft // 2 + 1
    mels = np.linspace(_hz_to_mel(mfcc["fmin_hz"]), _hz_to_mel(mfcc["fmax_hz"]), n_mels + 2)
    bins = np.floor((n_fft + 1) * _mel_to_hz(mels) / sr).astype(int)
    bins = np.clip(bins, 0, n_freq - 1)
    bank = np.zeros((n_mels, n_freq), dtype=np.float64)
    for i in range(n_mels):
        left, center, right = int(bins[i]), int(bins[i + 1]), int(bins[i + 2])
        if center > left:
            for j in range(left, center):
                bank[i, j] = (j - left) / (center - left)
        if right > center:
            for j in range(center, right):
                bank[i, j] = (right - j) / (right - center)
    return bank


def _dct_basis(n_mfcc, n_mels):
    k = np.arange(n_mfcc, dtype=np.float64)[:, None]
    n = np.arange(n_mels, dtype=np.float64)[None, :]
    basis = np.cos(np.pi * k * (n + 0.5) / n_mels)
    scale = np.full(n_mfcc, np.sqrt(2.0 / n_mels), dtype=np.float64)
    scale[0] = np.sqrt(1.0 / n_mels)
    return basis * scale[:, None]


def mfcc_from_pcm(samples, config):
    """Devolve o tensor (n_frames, n_mfcc) em float64."""
    audio = config["audio"]
    mfcc = config["mfcc"]
    if samples.shape[0] != audio["window_samples"]:
        raise ValueError("janela fora do contrato")

    x = samples.astype(np.float64)
    pre = mfcc["preemphasis"]
    y = np.empty_like(x)
    y[0] = x[0]
    y[1:] = x[1:] - pre * x[:-1]

    frame = mfcc["frame_length_samples"]
    hop = mfcc["frame_step_samples"]
    n_frames = mfcc["n_frames"]
    n_fft = mfcc["n_fft"]
    if mfcc["window_fn"] != "hann":
        raise ValueError("só a janela Hann está no contrato")

    n = np.arange(frame, dtype=np.float64)
    hann = 0.5 - 0.5 * np.cos(2.0 * np.pi * n / (frame - 1))
    bank = _mel_filterbank(config)
    basis = _dct_basis(mfcc["n_mfcc"], mfcc["n_mels"])
    lift_n = np.arange(mfcc["n_mfcc"], dtype=np.float64)
    lifter = 1.0 + (mfcc["lifter"] / 2.0) * np.sin(np.pi * lift_n / mfcc["lifter"])
    floor = mfcc["log_floor"]

    out = np.empty((n_frames, mfcc["n_mfcc"]), dtype=np.float64)
    for i in range(n_frames):
        start = i * hop
        chunk = y[start : start + frame]
        if chunk.shape[0] != frame:
            raise ValueError(f"quadro {i} não cabe na janela")
        spec = np.fft.rfft(chunk * hann, n=n_fft)
        power = (spec.real ** 2) + (spec.imag ** 2)
        mel = bank @ power
        log_mel = np.log(np.maximum(mel, floor))
        out[i] = log_mel @ basis.T
    if mfcc["include_energy"]:
        raise ValueError("o contrato não troca o c0 por energia")
    out *= lifter
    return out
