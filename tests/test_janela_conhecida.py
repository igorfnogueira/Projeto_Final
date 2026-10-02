"""Prova da janela conhecida: o transcript do PC, não o interno do MFCC."""

import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

ESPERADO = [
    "classe silencio",
    "classe desconhecido",
    "classe abrir",
    "classe fechar",
]


class JanelaConhecida(unittest.TestCase):
    def test_transcript_das_quatro_classes(self):
        proc = subprocess.run(
            [sys.executable, "-m", "treino.transcript"],
            cwd=ROOT,
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(proc.returncode, 0, proc.stderr)
        classes = [ln for ln in proc.stdout.splitlines() if ln.startswith("classe ")]
        self.assertEqual(classes, ESPERADO)
        diffs = [ln for ln in proc.stdout.splitlines() if ln.startswith("diferenca ")]
        self.assertEqual(len(diffs), 1)
        valor = float(diffs[0].split()[1])
        self.assertGreaterEqual(valor, 0.0)


if __name__ == "__main__":
    unittest.main()
