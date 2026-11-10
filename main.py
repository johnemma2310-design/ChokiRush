"""Punto de entrada.

Escritorio:  python main.py
Navegador:   python herramientas/construir_web.py   (compila con pygbag)
"""
import asyncio

import pygame          # noqa: F401  (pygbag detecta las dependencias leyendo estos imports)
import pygame.mixer    # noqa: F401

from roadrush.juego import Juego


async def main():
    await Juego().ejecutar()


asyncio.run(main())
