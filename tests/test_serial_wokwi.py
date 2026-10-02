"""Prova do serial no Wokwi: classe e servo, não o duty do LEDC."""

import subprocess
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
GCC = "gcc"
EXE = ROOT / "host" / "serial_demo.exe"

ESPERADO = (
    "classe silencio\n"
    "classe desconhecido\n"
    "classe abrir\n"
    "servo 90\n"
    "classe fechar\n"
    "servo 0\n"
)


class SerialWokwi(unittest.TestCase):
    def test_quatro_janelas_e_o_servo(self):
        compilou = subprocess.run(
            [
                GCC,
                "-O2",
                "-I",
                str(ROOT / "host"),
                "-o",
                str(EXE),
                str(ROOT / "host" / "serial_demo.c"),
                str(ROOT / "host" / "serial.c"),
            ],
            cwd=ROOT,
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(compilou.returncode, 0, compilou.stderr)
        proc = subprocess.run([str(EXE)], cwd=ROOT, capture_output=True, text=True, check=False)
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertEqual(proc.stdout, ESPERADO)


if __name__ == "__main__":
    unittest.main()
