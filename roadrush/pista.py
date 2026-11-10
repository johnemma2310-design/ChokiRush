"""Niveles y carretera procedural (curvas, anchos, decoración y líneas de salida/meta)."""
import math
import random
from dataclasses import dataclass
from typing import Optional

from . import config as C
from .fuente_pixel import FUENTE


@dataclass(frozen=True)
class Tema:
    pasto: tuple
    asfalto: tuple
    borde: tuple
    linea: tuple
    hojas: tuple
    hojas_luz: tuple
    hojas_osc: tuple
    tronco: tuple
    mancha: tuple
    mancha_brillo: tuple


TEMAS = {
    'ciudad': Tema(((62, 150, 62), (54, 138, 54)), ((86, 86, 96), (80, 80, 90)),
                   ((220, 50, 50), (240, 240, 240)), (245, 215, 80),
                   (34, 110, 44), (80, 170, 70), (20, 80, 34), (110, 70, 36),
                   (24, 24, 30), (90, 90, 120)),
    'costa': Tema(((222, 190, 120), (210, 176, 108)), ((112, 102, 98), (104, 95, 92)),
                  ((230, 110, 40), (250, 240, 220)), (255, 255, 255),
                  (40, 150, 80), (110, 200, 90), (26, 110, 60), (140, 95, 50),
                  (30, 26, 24), (110, 100, 90)),
    'nieve': Tema(((232, 238, 248), (216, 226, 242)), ((92, 100, 118), (86, 94, 112)),
                  ((50, 110, 220), (250, 250, 255)), (250, 250, 255),
                  (30, 90, 60), (240, 248, 255), (16, 64, 44), (90, 60, 40),
                  (150, 210, 240), (235, 250, 255)),
    'neon': Tema(((24, 22, 48), (30, 28, 58)), ((44, 42, 58), (40, 38, 54)),
                 ((255, 40, 190), (40, 240, 255)), (40, 255, 200),
                 (60, 30, 110), (255, 60, 200), (30, 16, 60), (60, 240, 255),
                 (120, 40, 200), (255, 120, 255)),
}


@dataclass(frozen=True)
class Nivel:
    numero: int
    nombre: str
    tema: Tema
    longitud: float
    ancho: float
    var_ancho: float
    curvatura: float
    frecuencia: float
    distancia_trafico: float
    enemigos: tuple                       # ((tipo, peso), ...)
    intervalo_manchas: Optional[tuple]    # None = sin manchas
    intervalo_escudo: tuple


NIVELES = (
    Nivel(1, "AVENIDA CENTRAL", TEMAS['ciudad'], 8000, 150, 18, 24, 0.0011, 260,
          (('civil', 7), ('zigzag', 1), ('camion', 2)), None, (3500, 5000)),
    Nivel(2, "COSTA DORADA", TEMAS['costa'], 10000, 140, 24, 30, 0.0014, 215,
          (('civil', 5), ('zigzag', 2), ('camion', 2), ('rival', 1)), (1000, 1700), (3500, 5000)),
    Nivel(3, "PASO NEVADO", TEMAS['nieve'], 12000, 128, 22, 36, 0.0017, 180,
          (('civil', 4), ('zigzag', 2), ('camion', 2), ('rival', 2)), (650, 1150), (3800, 5500)),
    Nivel(4, "CIUDAD NEÓN", TEMAS['neon'], 14000, 116, 22, 44, 0.0020, 145,
          (('civil', 3), ('zigzag', 3), ('camion', 2), ('rival', 3)), (750, 1300), (4000, 6000)),
)

INICIO_SALIDA = 40


class Pista:
    """Carretera infinita definida por funciones de la distancia recorrida `d`."""

    PASO_DECO = 34

    def __init__(self, nivel, ancho_area, recursos):
        self._nivel = nivel
        self._ancho_area = ancho_area
        self._cx = ancho_area / 2
        self._recursos = recursos

    @property
    def nivel(self):
        return self._nivel

    def _acotar(self, d):
        return min(max(d, 0.0), self._nivel.longitud)

    @staticmethod
    def _suavizado(d):
        # la salida es recta y las curvas aparecen poco a poco
        return min(1.0, max(0.0, (d - 120) / 500))

    def centro(self, d):
        d = self._acotar(d)
        n = self._nivel
        f = n.frecuencia
        onda = 0.7 * math.sin(d * f) + 0.3 * math.sin(d * f * 2.7 + 1.3)
        return self._cx + n.curvatura * self._suavizado(d) * onda

    def ancho(self, d):
        d = self._acotar(d)
        n = self._nivel
        return n.ancho + n.var_ancho * self._suavizado(d) * math.sin(d * n.frecuencia * 0.55 + 2.0)

    def limites(self, d):
        c = self.centro(d)
        m = self.ancho(d) / 2
        return c - m, c + m

    # ---------- dibujo ----------
    def dibujar(self, sup, camara):
        tema = self._nivel.tema
        w = self._ancho_area
        meta = self._nivel.longitud
        for sy in range(0, C.ALTO, 2):
            d = camara + (C.JUGADOR_Y - sy)
            izq, der = self.limites(d)
            il, dr = int(izq), int(der)
            franja = int(d // 24) % 2
            sup.fill(tema.pasto[franja], (0, sy, w, 2))
            sup.fill(tema.asfalto[franja], (il, sy, dr - il, 2))
            borde = tema.borde[int(d // 10) % 2]
            sup.fill(borde, (il, sy, 4, 2))
            sup.fill(borde, (dr - 4, sy, 4, 2))
            if int(d // 28) % 2 == 0:
                sup.fill(tema.linea, ((il + dr) // 2 - 1, sy, 2, 2))
            if INICIO_SALIDA <= d < INICIO_SALIDA + 12 or meta <= d < meta + 16:
                fila = int(d // 4)
                for x in range(il + 4, dr - 4, 4):
                    color = (245, 245, 245) if ((x - il) // 4 + fila) % 2 else (20, 20, 28)
                    sup.fill(color, (x, sy, min(4, dr - 4 - x), 2))
        self._dibujar_decoracion(sup, camara)
        sy_meta = C.JUGADOR_Y - (meta + 34 - camara)
        if -20 < sy_meta < C.ALTO:
            FUENTE.texto(sup, "META", int(self.centro(meta)), int(sy_meta), escala=2,
                         color=(255, 214, 64), alinear='centro')

    def _dibujar_decoracion(self, sup, camara):
        tema = self._nivel.tema
        k0 = int((camara - (C.ALTO - C.JUGADOR_Y) - 20) // self.PASO_DECO)
        k1 = int((camara + C.JUGADOR_Y + 20) // self.PASO_DECO) + 1
        for k in range(k0, k1):
            rng = random.Random(k * 7919 + self._nivel.numero * 104729)
            d = k * self.PASO_DECO
            sy = C.JUGADOR_Y - (d - camara)
            izq, der = self.limites(d)
            for _ in range(2):
                if rng.random() > 0.55:
                    continue
                spr = self._recursos.decoracion(tema, 0 if rng.random() < 0.6 else 1)
                sep = rng.uniform(9, 70)
                x = izq - sep if rng.random() < 0.5 else der + sep
                sup.blit(spr, (int(x - spr.get_width() / 2), int(sy - spr.get_height())))
