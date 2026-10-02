"""Treino do primeiro INT8 com os 30 clipes de Igor.

Caminhos lidos pelo treino:

- dataset/igor/abrir_01.wav … abrir_10.wav
- dataset/igor/fechar_01.wav … fechar_10.wav
- dataset/igor/silencio_01.wav … silencio_10.wav
- dataset/desconhecido/desconhecido_01.wav … desconhecido_10.wav

Os clipes 01 a 08 de cada classe treinam. Os 09 e 10 ficam de fora.
A seed é 42.
"""

import json
import os
import urllib.request
import zipfile
from pathlib import Path

os.environ.setdefault("TF_ENABLE_ONEDNN_OPTS", "0")

import numpy as np

from treino.mfcc import load_config, mfcc_from_pcm, read_pcm16_mono

ROOT = Path(__file__).resolve().parents[1]
IGOR = ROOT / "dataset" / "igor"
DESCONHECIDO = ROOT / "dataset" / "desconhecido"
CACHE = ROOT / "dataset" / ".cache"
SAIDA = ROOT / "treino" / "saida"
SEED = 42
MINI_URL = "https://storage.googleapis.com/download.tensorflow.org/data/mini_speech_commands.zip"
SPEECH_WORDS = ("down", "go", "left", "no", "right")
LABELS = ("silencio", "desconhecido", "abrir", "fechar")


def _write_wav(path, samples, rate):
    import struct

    data = np.asarray(samples, dtype="<i2").tobytes()
    header = struct.pack(
        "<4sI4s4sIHHIIHH4sI",
        b"RIFF",
        36 + len(data),
        b"WAVE",
        b"fmt ",
        16,
        1,
        1,
        rate,
        rate * 2,
        2,
        16,
        b"data",
        len(data),
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(header + data)


def _scale_to_pcm(x):
    peak = np.max(np.abs(x))
    if peak == 0:
        return np.zeros(x.shape[0], dtype=np.int16)
    y = x / peak * 8000.0
    return np.clip(np.round(y), -32768, 32767).astype(np.int16)


def _noise_clips(rate, n, rng):
    t = np.arange(n, dtype=np.float64) / rate
    white = rng.normal(size=n)
    pink = np.cumsum(rng.normal(size=n))
    tone = np.sin(2 * np.pi * 440 * t)
    two = np.sin(2 * np.pi * 220 * t) + 0.5 * np.sin(2 * np.pi * 660 * t)
    rumble = np.sin(2 * np.pi * 80 * t) * (0.5 + 0.5 * np.sin(2 * np.pi * 3 * t))
    return (
        ("01", _scale_to_pcm(white)),
        ("03", _scale_to_pcm(pink)),
        ("05", _scale_to_pcm(tone)),
        ("07", _scale_to_pcm(two)),
        ("09", _scale_to_pcm(rumble)),
    )


def _ensure_desconhecido(config):
    rate = config["audio"]["sample_rate_hz"]
    n = config["audio"]["window_samples"]
    needed = [DESCONHECIDO / f"desconhecido_{i:02d}.wav" for i in range(1, 11)]
    if all(p.is_file() for p in needed):
        return

    rng = np.random.default_rng(SEED)
    for suffix, pcm in _noise_clips(rate, n, rng):
        _write_wav(DESCONHECIDO / f"desconhecido_{suffix}.wav", pcm, rate)

    CACHE.mkdir(parents=True, exist_ok=True)
    zip_path = CACHE / "mini_speech_commands.zip"
    if not zip_path.is_file():
        urllib.request.urlretrieve(MINI_URL, zip_path)
    extract = CACHE / "mini_speech_commands"
    if not extract.is_dir():
        with zipfile.ZipFile(zip_path) as zf:
            zf.extractall(CACHE)

    speech_suffixes = ("02", "04", "06", "08", "10")
    for word, suffix in zip(SPEECH_WORDS, speech_suffixes):
        folder = extract / word
        if not folder.is_dir():
            folder = extract / "mini_speech_commands" / word
        wavs = sorted(folder.glob("*.wav"))
        if not wavs:
            raise FileNotFoundError(f"sem WAV público em {folder}")
        src = wavs[0]
        samples = _fit_window(src, config)
        _write_wav(DESCONHECIDO / f"desconhecido_{suffix}.wav", samples, rate)


def _fit_window(path, config):
    """Recorta ou completa com silêncio até a janela. Não estica o tempo."""
    import struct

    rate = config["audio"]["sample_rate_hz"]
    window = config["audio"]["window_samples"]
    with open(path, "rb") as f:
        riff, _, wave = struct.unpack("<4sI4s", f.read(12))
        if riff != b"RIFF" or wave != b"WAVE":
            raise ValueError(path)
        fmt = None
        samples = None
        while True:
            hdr = f.read(8)
            if len(hdr) < 8:
                break
            cid, csize = struct.unpack("<4sI", hdr)
            start = f.tell()
            if cid == b"fmt ":
                fmt = struct.unpack("<HHIIHH", f.read(16))
            elif cid == b"data":
                samples = np.frombuffer(f.read(csize), dtype="<i2").copy()
            f.seek(start + csize + (csize % 2))
    audio_format, channels, file_rate, _, _, bits = fmt
    if (audio_format, channels, file_rate, bits) != (1, 1, rate, 16):
        raise ValueError(f"WAV público fora do contrato: {path}")
    if samples.shape[0] >= window:
        start = (samples.shape[0] - window) // 2
        return samples[start : start + window]
    out = np.zeros(window, dtype=np.int16)
    out[: samples.shape[0]] = samples
    return out


def _paths():
    groups = {
        "abrir": IGOR,
        "fechar": IGOR,
        "silencio": IGOR,
        "desconhecido": DESCONHECIDO,
    }
    rows = []
    for label, folder in groups.items():
        for i in range(1, 11):
            path = folder / f"{label}_{i:02d}.wav"
            rows.append((label, i, path))
    return rows


def load_dataset(config):
    _ensure_desconhecido(config)
    features = []
    labels = []
    paths = []
    split = []
    index = {name: i for i, name in enumerate(LABELS)}
    for label, i, path in _paths():
        if not path.is_file():
            raise FileNotFoundError(path)
        pcm = read_pcm16_mono(path, config)
        features.append(mfcc_from_pcm(pcm, config).astype(np.float32))
        labels.append(index[label])
        paths.append(str(path.relative_to(ROOT)).replace("\\", "/"))
        split.append("train" if i <= 8 else "test")
    x = np.stack(features)
    y = np.asarray(labels, dtype=np.int32)
    expected = tuple(config["tensor"]["shape"])
    if x.shape[1:] != expected:
        raise ValueError(f"tensor {x.shape[1:]} != {expected}")
    return x, y, paths, split


def _build_model(x_train, y_train):
    import tensorflow as tf

    class CentroidLogits(tf.keras.layers.Layer):
        def __init__(self, n_classes):
            super().__init__()
            self.n_classes = n_classes

        def build(self, input_shape):
            self.templates = self.add_weight(
                name="templates",
                shape=(self.n_classes,) + tuple(input_shape[1:]),
                initializer="zeros",
                trainable=False,
            )

        def call(self, x):
            diff = x[:, None, :, :] - self.templates[None, :, :, :]
            return -tf.reduce_mean(tf.square(diff), axis=[2, 3])

    templates = np.stack(
        [x_train[y_train == c].mean(axis=0) for c in range(len(LABELS))]
    ).astype(np.float32)
    inputs = tf.keras.Input(shape=x_train.shape[1:])
    logits = CentroidLogits(len(LABELS))(inputs)
    model = tf.keras.Model(inputs, logits)
    model(x_train[:1])
    model.layers[-1].set_weights([templates])
    return model


def _to_int8(model, x_train):
    import tensorflow as tf

    converter = tf.lite.TFLiteConverter.from_keras_model(model)
    converter.optimizations = [tf.lite.Optimize.DEFAULT]

    def representative():
        for row in x_train:
            yield [row[None, ...]]

    converter.representative_dataset = representative
    converter.target_spec.supported_ops = [tf.lite.OpsSet.TFLITE_BUILTINS_INT8]
    converter.inference_input_type = tf.int8
    converter.inference_output_type = tf.int8
    return converter.convert()


def _predict_int8(tflite_bytes, rows):
    import tensorflow as tf

    interpreter = tf.lite.Interpreter(model_content=tflite_bytes)
    interpreter.allocate_tensors()
    inp = interpreter.get_input_details()[0]
    out = interpreter.get_output_details()[0]
    classes = []
    logits = []
    for row in rows:
        quantized = row / inp["quantization"][0] + inp["quantization"][1]
        quantized = np.clip(np.round(quantized), -128, 127).astype(np.int8)
        interpreter.set_tensor(inp["index"], quantized[None, ...])
        interpreter.invoke()
        raw = interpreter.get_tensor(out["index"])[0]
        scale, zero = out["quantization"]
        value = (raw.astype(np.float32) - zero) * scale
        logits.append(value)
        classes.append(int(np.argmax(value)))
    return np.asarray(classes), np.stack(logits), inp["quantization"], out["quantization"]


def main():
    import tensorflow as tf

    tf.keras.utils.set_random_seed(SEED)
    config = load_config()
    if config["labels"] != list(LABELS):
        raise ValueError("a ordem das classes no config mudou")

    x, y, paths, split = load_dataset(config)
    train = np.array([s == "train" for s in split])
    test = ~train
    model = _build_model(x[train], y[train])
    train_pred = np.argmax(model.predict(x[train], verbose=0), axis=1)
    test_pred = np.argmax(model.predict(x[test], verbose=0), axis=1)
    train_acc = float(np.mean(train_pred == y[train]))
    test_acc = float(np.mean(test_pred == y[test]))

    SAIDA.mkdir(parents=True, exist_ok=True)
    tflite = _to_int8(model, x[train])
    (SAIDA / "modelo.tflite").write_bytes(tflite)
    pred, logits, in_q, out_q = _predict_int8(tflite, x[test])
    int8_acc = float(np.mean(pred == y[test]))

    test_positions = {idx: n for n, idx in enumerate(np.where(test)[0])}
    golden_idx = [i for i, (p, s) in enumerate(zip(paths, split)) if s == "test" and p.endswith("_09.wav")]
    golden = []
    for i in golden_idx:
        slot = test_positions[i]
        golden.append(
            {
                "path": paths[i],
                "label": LABELS[int(y[i])],
                "pred": LABELS[int(pred[slot])],
                "logits_int8": logits[slot].tolist(),
            }
        )

    np.savez(
        SAIDA / "vetor_dourado.npz",
        paths=np.array([g["path"] for g in golden]),
        labels=np.array([g["label"] for g in golden]),
        pred=np.array([g["pred"] for g in golden]),
        mfcc=np.stack([x[i] for i in golden_idx]),
        logits=np.stack([logits[test_positions[i]] for i in golden_idx]),
    )
    metrics = {
        "seed": SEED,
        "labels": list(LABELS),
        "n_train": int(train.sum()),
        "n_test": int(test.sum()),
        "modelo": "centroide",
        "epochs": 0,
        "acc_treino_float": train_acc,
        "acc_teste_float": test_acc,
        "acc_teste_int8": int8_acc,
        "input_quantization": {"scale": float(in_q[0]), "zero_point": int(in_q[1])},
        "output_quantization": {"scale": float(out_q[0]), "zero_point": int(out_q[1])},
        "golden": [
            {"path": g["path"], "label": g["label"], "pred": g["pred"]} for g in golden
        ],
        "teste": [
            {"path": paths[i], "label": LABELS[int(y[i])], "pred": LABELS[int(pred[test_positions[i]])]}
            for i in np.where(test)[0]
        ],
    }
    (SAIDA / "metricas.json").write_text(json.dumps(metrics, indent=2), encoding="utf-8")
    print(json.dumps({k: metrics[k] for k in ("acc_treino_float", "acc_teste_float", "acc_teste_int8", "teste")}, indent=2))
    return metrics


if __name__ == "__main__":
    main()
