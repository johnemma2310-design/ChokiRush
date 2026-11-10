"""Pixel art original del juego, definido como plantillas de texto + paletas de color.

Cada caracter de una plantilla es un pixel; la paleta traduce el caracter a un color.
'.' (o cualquier caracter fuera de la paleta) es transparente. Así el mismo dibujo
sirve para muchos autos con solo cambiar la paleta.
"""
import os

import pygame

from . import config as C

CONTORNO = (20, 20, 30)

PLANTILLA_AUTO = (
    "...KKKKKK...",
    "..KBBBBBBK..",
    ".KYBLTTLBYK.",
    ".KBBLTTLBBK.",
    "KKBBBBBBBBKK",
    "KKDWWWWWWDKK",
    "KKDWSWWWWDKK",
    ".KDDBBBBDDK.",
    ".KBBLTTLBBK.",
    ".KBBLTTLBBK.",
    ".KBBLTTLBBK.",
    ".KBBBBBBBBK.",
    "KKDWWWWWWDKK",
    "KKDBBBBBBDKK",
    "KKBBBBBBBBKK",
    ".KRBBBBBBRK.",
    "..KKKKKKKK..",
)

PLANTILLA_CAMION = (
    "..KKKKKKKKKK..",
    ".KCCCCCCCCCCK.",
    ".KYCCCCCCCCYK.",
    "KKCWWWWWWWWCKK",
    "KKCWSWWWWWWCKK",
    "KKCCCCCCCCCCKK",
    ".KKKKKKKKKKKK.",
    ".KGGGGGGGGGGK.",
    "KKGHHHHHHHHGKK",
    "KKGGGGGGGGGGKK",
    ".KGHHHHHHHHGK.",
    ".KGGGGGGGGGGK.",
    ".KGHHHHHHHHGK.",
    ".KGGGGGGGGGGK.",
    ".KGHHHHHHHHGK.",
    ".KGGGGGGGGGGK.",
    "KKGHHHHHHHHGKK",
    "KKGGGGGGGGGGKK",
    "KKGHHHHHHHHGKK",
    ".KGGGGGGGGGGK.",
    ".KRKKKKKKKKRK.",
    "..KKKKKKKKKK..",
)

# Cara genérica del profe (se usa si no hay foto en assets/profesor.png)
PLANTILLA_CARA = (
    "....KKKKKK....",
    "..KKHHHHHHKK..",
    ".KHHHHHHHHHHK.",
    ".KHSSSSSSSSHK.",
    "KHSSSSSSSSSSHK",
    "KSGGGGSSGGGGSK",
    "KSGWEGGGGWEGSK",
    "KSGGGGSSGGGGSK",
    "KSSSSSssSSSSSK",
    ".KSSSSSSSSSSK.",
    ".KSMSSSSSSMSK.",
    "..KSMMMMMMSK..",
    "...KKSSSSKK...",
    ".....KKKK.....",
)
PALETA_CARA = {
    'K': CONTORNO, 'H': (70, 52, 40), 'S': (240, 196, 150), 's': (206, 156, 112),
    'G': (30, 30, 40), 'W': (200, 235, 255), 'E': (30, 30, 40), 'M': (150, 50, 50),
}

PLANTILLA_CASCO = (
    "....KKKKKK....",
    "..KKCCCCCCKK..",
    ".KCCCTTTTCCCK.",
    ".KCCTTTTTTCCK.",
    "KCCCCCCCCCCCCK",
    "KCCKKKKKKKKCCK",
    "KCKVVVVVVVVKCK",
    "KCKVLVVVVVVKCK",
    "KCKVVVVVVVVKCK",
    "KCCKKKKKKKKCCK",
    ".KCCCCCCCCCCK.",
    ".KDCCCCCCCCDK.",
    "..KDDDDDDDDK..",
    "...KKKKKKKK...",
)

PLANTILLA_GASOLINA = (
    "..KKKKK...",
    "..KYYYK...",
    ".KKKKKKKK.",
    "KRRRRRRRRK",
    "KRLRRRRRRK",
    "KRRWRRRWRK",
    "KRRRWRWRRK",
    "KRRRRWRRRK",
    "KRRRWRWRRK",
    "KRRWRRRWRK",
    "KRRRRRRRRK",
    ".KKKKKKKK.",
)

PLANTILLA_ESCUDO = (
    "KKKKKKKKKKKK",
    "KBBBBBBBBBBK",
    "KBLLBBBBBBBK",
    "KBLBBWWBBBBK",
    "KBBBWWWWBBBK",
    "KBBBBWWBBBBK",
    ".KBBBBBBBBK.",
    ".KBBBBBBBBK.",
    "..KBBBBBBK..",
    "...KBBBBK...",
    "....KBBK....",
    ".....KK.....",
)

PLANTILLA_MANCHA = (
    "....AAAAA.......",
    "..AAAAAAAAA.....",
    ".AAAOAAAAAAAA...",
    "AAAAOOAAAAAAAAA.",
    ".AAAAAAAAOAAAAAA",
    "..AAAAAAAAAAAA..",
    "....AAAAAAA.....",
    "......AAA.......",
)

PLANTILLA_ARBOL = (
    "...GGGG...",
    "..GGLGGG..",
    ".GGLGGGGG.",
    "GGGGGGGGGG",
    "GLGGGGGDGG",
    ".GGGGGDGG.",
    "GGGGGDDGGG",
    ".GGDDDDGG.",
    "..GGGGGG..",
    "....TT....",
    "....TT....",
    "...TTTT...",
)

PLANTILLA_ARBUSTO = (
    "..GGGG..",
    ".GLGGGG.",
    "GGGGGLGG",
    "GGDGGGGG",
    ".GGGDGG.",
    "..GGGG..",
)


# Cuerpo del muñeco (traje de piloto). Dos cuadros para animar las piernas.
PLANTILLAS_CUERPO = (
    (
        "...KKKKKKKK...",
        "..KCCCWWCCCK..",
        ".KCCCCWWCCCCK.",
        "KCKCCCWWCCCKCK",
        "KCKCCCWWCCCKCK",
        "KSKCCCWWCCCKSK",
        ".K.KDDDDDDK.K.",
        "...KDDKKDDK...",
        "...KDDKKDDK...",
        "...KDDKKDDK...",
        "..KKKK..KKKK..",
    ),
    (
        "...KKKKKKKK...",
        "..KCCCWWCCCK..",
        ".KCCCCWWCCCCK.",
        "KCKCCCWWCCCKCK",
        "KCKCCCWWCCCKCK",
        "KSKCCCWWCCCKSK",
        ".K.KDDDDDDK.K.",
        "..KDDK..KDDK..",
        "..KDDK..KDDK..",
        ".KDDK....KDDK.",
        ".KKKK....KKKK.",
    ),
)

PLANTILLA_CORONA = (
    "K..K..K..K",
    "KY.KY.KY.K",
    "KYYKYYKYYK",
    "KYYYRYYYYK",
    "KOOOOOOOOK",
    "KKKKKKKKKK",
)


def construir(plantilla, paleta):
    """Convierte una plantilla de texto en una Surface con transparencia."""
    alto = len(plantilla)
    ancho = max(len(fila) for fila in plantilla)
    sup = pygame.Surface((ancho, alto), pygame.SRCALPHA)
    for y, fila in enumerate(plantilla):
        for x, c in enumerate(fila):
            color = paleta.get(c)
            if color is not None:
                sup.set_at((x, y), color)
    return sup


def aclarar(color, k):
    return tuple(min(255, int(v + (255 - v) * k)) for v in color)


def oscurecer(color, k):
    return tuple(int(v * (1 - k)) for v in color)


def paleta_auto(base, franja=None):
    return {
        'K': CONTORNO, 'B': base, 'D': oscurecer(base, 0.35), 'L': aclarar(base, 0.25),
        'T': franja if franja else aclarar(base, 0.25), 'W': (100, 170, 225), 'S': (225, 245, 255),
        'Y': (255, 240, 150), 'R': (235, 40, 40),
    }


class Recursos:
    """Fábrica y caché de todos los sprites del juego."""

    def __init__(self):
        self._cache = {}
        self.usa_foto = False
        self.cara_profe = self._crear_moneda_profe()

    def _memo(self, clave, fabrica):
        sup = self._cache.get(clave)
        if sup is None:
            sup = fabrica()
            self._cache[clave] = sup
        return sup

    # ---------- cara del profe ----------
    def _cara_desde_foto(self):
        """Usa el mismo pixelador de los pilotos (detecta la cara y quita el fondo)."""
        from .pixelador import Pixelador
        for ruta in C.RUTAS_FOTO_PROFE:
            if not os.path.isfile(ruta):
                continue
            try:
                with open(ruta, "rb") as f:
                    sprite = Pixelador(tam=18, colores=9).procesar(f.read(), os.path.basename(ruta))
            except (OSError, ValueError):
                continue
            self.usa_foto = True
            return sprite.a_superficie()
        return None

    def _imagen(self, ruta):
        """Carga una imagen de assets una sola vez (None si no existe)."""
        def fabrica():
            try:
                return pygame.image.load(ruta)
            except (pygame.error, OSError, FileNotFoundError):
                return False
        img = self._memo(('img', ruta), fabrica)
        return img or None

    def _cara_moneda_dialogo(self):
        """Cara redonda para la moneda, recortada de la imagen del diálogo (primer plano del profe)."""
        img = self._imagen(C.RUTA_PROFE_DIALOGO)
        if img is None:
            return None
        w, h = img.get_size()
        lado = int(min(w, h) * 0.72)
        cuadro = pygame.Surface((lado, lado), pygame.SRCALPHA)
        cuadro.blit(img, (-(w // 2 - lado // 2), -(int(h * 0.47) - lado // 2)))
        cara = pygame.transform.smoothscale(cuadro, (20, 20))
        for y in range(20):
            for x in range(20):
                if (x - 9.5) ** 2 + (y - 9.5) ** 2 > 9.7 ** 2:
                    cara.set_at((x, y), (0, 0, 0, 0))
        self.usa_foto = True
        return cara

    def retrato_dialogo(self, alto):
        """Cara del profe para los cuadros de diálogo (fondo azul, estilo RPG)."""
        def fabrica():
            img = self._imagen(C.RUTA_PROFE_DIALOGO)
            if img is None:
                return pygame.transform.scale(self.cara_profe, (alto, alto))
            ancho = round(img.get_width() * alto / img.get_height())
            return pygame.transform.smoothscale(img.convert_alpha(), (ancho, alto))
        return self._memo(('dialogo', alto), fabrica)

    def profe_senalando(self, alto):
        """El profe de cuerpo entero señalando (sin el fondo blanco). None si no hay imagen."""
        def fabrica():
            from collections import deque
            img = None
            for ruta in C.RUTAS_FOTO_PROFE:
                img = self._imagen(ruta)
                if img is not None:
                    break
            if img is None:
                return False
            ancho = round(img.get_width() * alto / img.get_height())
            sup = pygame.Surface((ancho, alto), pygame.SRCALPHA)
            sup.blit(pygame.transform.smoothscale(img.convert_alpha(), (ancho, alto)), (0, 0))
            visto = set()
            cola = deque([(x, y) for x in range(ancho) for y in (0, alto - 1)] +
                         [(x, y) for y in range(alto) for x in (0, ancho - 1)])
            while cola:                                   # borra el blanco conectado al borde
                x, y = cola.popleft()
                if not (0 <= x < ancho and 0 <= y < alto) or (x, y) in visto:
                    continue
                visto.add((x, y))
                r, g, b, a = sup.get_at((x, y))
                if a > 0 and min(r, g, b) < 215:
                    continue
                sup.set_at((x, y), (0, 0, 0, 0))
                cola.extend(((x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)))
            return sup
        return self._memo(('senalando', alto), fabrica) or None

    def _crear_moneda_profe(self):
        cara = self._cara_moneda_dialogo() or self._cara_desde_foto()
        lado = 26 if cara is not None else 22          # con foto, moneda más grande para ver la cara
        c = lado // 2
        sup = pygame.Surface((lado, lado), pygame.SRCALPHA)
        pygame.draw.circle(sup, (110, 70, 10), (c, c), c)
        pygame.draw.circle(sup, (255, 210, 60), (c, c), c - 1)
        pygame.draw.circle(sup, (205, 145, 25), (c, c), c - 2)
        cara = cara or construir(PLANTILLA_CARA, PALETA_CARA)
        sup.blit(cara, (c - cara.get_width() // 2, c - cara.get_height() // 2 + 1))
        for p in ((4, 6), (5, 4), (6, 3)):
            sup.set_at(p, (255, 250, 210))
        return sup

    # ---------- vehículos ----------
    def auto(self, base, franja=None):
        return self._memo(('auto', base, franja),
                          lambda: construir(PLANTILLA_AUTO, paleta_auto(base, franja)))

    def auto_jugador(self, personaje):
        return self.auto(personaje.color_auto, personaje.color_franja)

    def camion(self, cabina, carga):
        def fabrica():
            paleta = {'K': CONTORNO, 'C': cabina, 'Y': (255, 240, 150), 'W': (100, 170, 225),
                      'S': (225, 245, 255), 'G': carga, 'H': aclarar(carga, 0.35), 'R': (235, 40, 40)}
            return construir(PLANTILLA_CAMION, paleta)
        return self._memo(('camion', cabina, carga), fabrica)

    def cabeza(self, sprite):
        """Superficie de un SpritePixel (cara pixelada o casco). El sprite es su propia clave."""
        return self._memo(('cabeza', sprite), sprite.a_superficie)

    def retrato(self, personaje):
        return self.cabeza(personaje.cabeza())

    def retrato_grande(self, sprite, lado=None):
        """Retrato HD (211 px). Con `lado` se reduce suavemente para vistas previas."""
        base = self.cabeza(sprite)
        if lado is None:
            return base
        return self._memo(('rg', sprite, lado), lambda: pygame.transform.smoothscale(base, (lado, lado)))

    def muneco(self, sprite_cabeza, color, cuadro=0):
        """Muñeco de cuerpo entero: cabeza (foto pixelada o casco) + traje de piloto."""
        def fabrica():
            cabeza = self.cabeza(sprite_cabeza)
            paleta = {'K': CONTORNO, 'C': color, 'D': oscurecer(color, 0.45), 'W': (250, 250, 250),
                      'S': (240, 196, 150)}
            cuerpo = construir(PLANTILLAS_CUERPO[cuadro % len(PLANTILLAS_CUERPO)], paleta)
            ancho = max(cabeza.get_width(), cuerpo.get_width())
            alto = cabeza.get_height() + cuerpo.get_height() - 1
            sup = pygame.Surface((ancho, alto), pygame.SRCALPHA)
            sup.blit(cuerpo, ((ancho - cuerpo.get_width()) // 2, cabeza.get_height() - 1))
            sup.blit(cabeza, ((ancho - cabeza.get_width()) // 2, 0))
            return sup
        return self._memo(('muneco', sprite_cabeza, tuple(color), cuadro % len(PLANTILLAS_CUERPO)), fabrica)

    def muneco_de(self, personaje, cuadro=0):
        return self.muneco(personaje.cabeza(), personaje.color_auto, cuadro)

    def corona(self):
        return self._memo('corona', lambda: construir(PLANTILLA_CORONA, {
            'K': CONTORNO, 'Y': (255, 214, 64), 'O': (220, 150, 20), 'R': (236, 64, 64)}))

    # ---------- objetos ----------
    def gasolina(self):
        return self._memo('gasolina', lambda: construir(PLANTILLA_GASOLINA, {
            'K': CONTORNO, 'R': (220, 40, 40), 'L': (255, 140, 140), 'W': (250, 250, 250), 'Y': (255, 210, 60)}))

    def escudo(self):
        return self._memo('escudo', lambda: construir(PLANTILLA_ESCUDO, {
            'K': CONTORNO, 'B': (50, 140, 240), 'L': (160, 220, 255), 'W': (255, 230, 80)}))

    def mancha(self, tema):
        return self._memo(('mancha', tema.mancha), lambda: construir(PLANTILLA_MANCHA, {
            'A': tema.mancha, 'O': tema.mancha_brillo}))

    def decoracion(self, tema, variante):
        plantilla = PLANTILLA_ARBOL if variante == 0 else PLANTILLA_ARBUSTO
        return self._memo(('deco', tema.hojas, variante), lambda: construir(plantilla, {
            'G': tema.hojas, 'L': tema.hojas_luz, 'D': tema.hojas_osc, 'T': tema.tronco}))

    def escalar(self, sup, k):
        return self._memo(('esc', id(sup), k),
                          lambda: pygame.transform.scale(sup, (sup.get_width() * k, sup.get_height() * k)))
