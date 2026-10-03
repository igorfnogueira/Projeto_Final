"""A janela do microfone usa o mesmo serial do firmware, sem abrir o microfone."""

import unittest
from pathlib import Path

from treino.mfcc import load_config, read_pcm16_mono
from treino.ouvir import _serial, texto_da_janela
from treino.transcript import JANELAS, ORDEM, _biblioteca, _contrato

ROOT = Path(__file__).resolve().parents[1]
ESPERADO = {
    "silencio": "classe silencio\n",
    "desconhecido": "classe desconhecido\n",
    "abrir": "classe abrir\nservo 90\n",
    "fechar": "classe fechar\nservo 0\n",
}


class Ouvir(unittest.TestCase):
    def test_janelas_conhecidas_tem_o_mesmo_serial(self):
        config = load_config()
        _contrato(config)
        lib_mfcc = _biblioteca()
        lib_serial = _serial()
        modelo = (ROOT / "treino" / "saida" / "modelo.tflite").read_bytes()
        for nome in ORDEM:
            pcm = read_pcm16_mono(JANELAS[nome], config)
            self.assertEqual(
                texto_da_janela(pcm, lib_mfcc, lib_serial, modelo),
                ESPERADO[nome],
            )


if __name__ == "__main__":
    unittest.main()
