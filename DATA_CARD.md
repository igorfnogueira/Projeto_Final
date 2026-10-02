# Data card

O primeiro treino, em 2026-10-02, usa uma voz do grupo: Igor. São 10 clipes de "abrir porta", 10 de "fechar porta" e 10 de silêncio, em `dataset/igor/`, nomes `abrir_01.wav` … `abrir_10.wav`, `fechar_01.wav` … `fechar_10.wav` e `silencio_01.wav` … `silencio_10.wav`. Os clipes 01 a 08 entram na média da classe. Os 09 e 10 ficam de fora.

A classe `desconhecido` não guarda voz de fora com identidade. São 5 ruídos gerados com a seed 42 (`desconhecido_01.wav`, `03`, `05`, `07`, `09`) e 5 clipes do mini Speech Commands, em inglês, sem nome de falante (`desconhecido_02.wav` down, `04` go, `06` left, `08` no, `10` right). Origem: <https://storage.googleapis.com/download.tensorflow.org/data/mini_speech_commands.zip>, licença CC BY 4.0. Os arquivos ficam em `dataset/desconhecido/`.

Os outros integrantes ainda não gravaram. <!-- PENDENTE: os demais nomes e a data em que cada um gravar -->

Licença dos clipes do grupo: ainda não declarada. <!-- PENDENTE: licença dos áudios gravados pelo grupo -->
