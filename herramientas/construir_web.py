"""Compila el juego para el navegador con pygbag y lo copia a web/juego/.

Uso:  python herramientas/construir_web.py
Luego se publica la carpeta web/ en Vercel (ver README).
"""
import os
import shutil
import subprocess
import sys

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def main():
    if not os.path.isfile(os.path.join(RAIZ, "assets", "audio", "indice.json")):
        subprocess.check_call([sys.executable, os.path.join(RAIZ, "herramientas", "generar_audio.py")])
    subprocess.check_call([sys.executable, "-m", "pygbag", "--build", "--app_name", "roadrush",
                           "--title", "Choki Rush", "--ume_block", "1", "."], cwd=RAIZ)
    origen = os.path.join(RAIZ, "build", "web")
    destino = os.path.join(RAIZ, "web", "juego")
    shutil.rmtree(destino, ignore_errors=True)
    shutil.copytree(origen, destino)
    print("Juego web listo en", destino)
    for nombre in sorted(os.listdir(destino)):
        print("  ", nombre, os.path.getsize(os.path.join(destino, nombre)), "bytes")


if __name__ == "__main__":
    main()
