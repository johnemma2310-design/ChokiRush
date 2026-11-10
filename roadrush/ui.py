"""Utilidades de interfaz: paneles, barras, velos y ajuste de texto."""
import pygame

from . import config as C

_cache = {}


def velo(sup, alfa=140, color=(0, 0, 0)):
    """Oscurece toda la superficie con un velo semitransparente."""
    clave = ('velo', sup.get_size(), alfa, color)
    v = _cache.get(clave)
    if v is None:
        v = pygame.Surface(sup.get_size(), pygame.SRCALPHA)
        v.fill((*color, alfa))
        _cache[clave] = v
    sup.blit(v, (0, 0))


def panel(sup, rect, borde=C.AMARILLO, alfa=215):
    r = pygame.Rect(rect)
    clave = ('panel', r.size, alfa)
    fondo = _cache.get(clave)
    if fondo is None:
        fondo = pygame.Surface(r.size, pygame.SRCALPHA)
        fondo.fill((16, 14, 32, alfa))
        _cache[clave] = fondo
    sup.blit(fondo, r.topleft)
    pygame.draw.rect(sup, borde, r, 1)
    # esquinas "biseladas" estilo pixel
    for (x, y) in (r.topleft, (r.right - 1, r.top), (r.left, r.bottom - 1), (r.right - 1, r.bottom - 1)):
        sup.set_at((x, y), (16, 14, 32))
    pygame.draw.rect(sup, (60, 52, 96), r.inflate(-4, -4), 1)


def barra(sup, rect, fraccion, color, fondo=(44, 40, 64), segmentos=0):
    r = pygame.Rect(rect)
    pygame.draw.rect(sup, fondo, r)
    w = int((r.w - 2) * max(0.0, min(1.0, fraccion)))
    if w > 0:
        sup.fill(color, (r.x + 1, r.y + 1, w, r.h - 2))
        sup.fill(tuple(min(255, c + 60) for c in color), (r.x + 1, r.y + 1, w, 1))
    for i in range(1, segmentos):
        sup.fill(fondo, (r.x + r.w * i // segmentos, r.y + 1, 1, r.h - 2))
    pygame.draw.rect(sup, (8, 8, 14), r, 1)


def envolver(texto, max_chars):
    """Parte un texto en líneas de como máximo `max_chars` caracteres."""
    lineas, actual = [], ""
    for palabra in texto.split():
        prueba = f"{actual} {palabra}".strip()
        if len(prueba) <= max_chars:
            actual = prueba
        else:
            if actual:
                lineas.append(actual)
            actual = palabra
    if actual:
        lineas.append(actual)
    return lineas
