"""Genera los .ogg del juego con el sintetizador propio (assets/audio/).

Uso:  python herramientas/generar_audio.py
El juego funciona sin estos archivos (los sintetiza al iniciar), pero en el navegador
cargarlos ya hechos es mucho más rápido.
"""
import json
import os
import sys

import numpy as np         # pip install soundfile numpy (solo para esta herramienta)
import soundfile as sf

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, RAIZ)

from roadrush import config as C                                    # noqa: E402
from roadrush.audio import GANANCIA_MUSICA, Sintetizador, componer_todo  # noqa: E402

FRECUENCIA = 22050


def main():
    os.makedirs(C.DIR_AUDIO, exist_ok=True)
    s = Sintetizador(FRECUENCIA)
    todo = componer_todo(s, lambda f, m: print(f"{int(f * 100):3d}%  {m}"))
    indice = {}
    for grupo, sonidos in todo.items():
        indice[grupo] = []
        for nombre, buf in sonidos.items():
            ganancia = GANANCIA_MUSICA.get(nombre, 1.0) if grupo == "musicas" else 1.0
            muestras = np.frombuffer(s.a_muestras(buf, ganancia).tobytes(), dtype=np.int16)
            sf.write(os.path.join(C.DIR_AUDIO, f"{nombre}.ogg"), muestras, FRECUENCIA,
                     format="OGG", subtype="VORBIS")
            indice[grupo].append(nombre)
    with open(os.path.join(C.DIR_AUDIO, "indice.json"), "w", encoding="utf-8") as f:
        json.dump(indice, f, indent=1)
    print("Listo:", C.DIR_AUDIO)


if __name__ == "__main__":
    main()
