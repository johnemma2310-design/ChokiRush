"""Pilotos: los 4 predefinidos y el piloto personalizado creado por el jugador."""
from dataclasses import dataclass
from typing import Optional

from .pixelador import SpritePixel, color_desde_hex
from .pixelart import PLANTILLA_CASCO, CONTORNO, oscurecer

PUNTOS_LIBRES = 8          # puntos que el jugador reparte al crear su piloto
NIVEL_MIN, NIVEL_MAX = 1, 5


def _normalizar(valor, minimo, maximo):
    return max(0.1, min(1.0, (valor - minimo) / (maximo - minimo)))


@dataclass(frozen=True)
class Personaje:
    nombre: str
    apodo: str
    descripcion: str
    color_auto: tuple
    color_franja: tuple
    color_casco: tuple
    color_visor: tuple
    velocidad_max: float   # unidades de mundo por segundo
    aceleracion: float
    manejo: float          # pixeles laterales por segundo
    eficiencia: float      # multiplicador de consumo (menor = gasta menos)

    @property
    def personalizado(self):
        return False

    def estadisticas(self):
        """Valores 0..1 para mostrar barras en la pantalla de selección."""
        return (
            ("VELOCIDAD", _normalizar(self.velocidad_max, 250, 310)),
            ("ACELERACIÓN", _normalizar(self.aceleracion, 135, 211)),
            ("MANEJO", _normalizar(self.manejo, 105, 189)),
            ("ECONOMÍA", _normalizar(1.3 - self.eficiencia, 0.05, 0.61)),
        )

    def cabeza(self):
        """Sprite de la cabeza del muñeco: un casco con los colores del piloto."""
        c = self.color_casco
        return SpritePixel.desde_plantilla(PLANTILLA_CASCO, {
            'K': CONTORNO, 'C': c, 'T': self.color_franja, 'D': oscurecer(c, 0.4),
            'V': self.color_visor, 'L': (240, 248, 255)})

    def resumen_online(self):
        """Lo que se envía a la clasificación para dibujar el muñeco en el podio."""
        return {"nombre": self.nombre, "color": "#%02x%02x%02x" % self.color_auto,
                "sprite": self.cabeza().a_dict()}


@dataclass(frozen=True)
class PersonajePersonalizado(Personaje):
    """Piloto creado por el jugador: su foto pixelada + puntos repartidos."""
    niveles: tuple = (3, 3, 3, 3)            # velocidad, aceleración, manejo, economía (1..5)
    sprite: Optional[SpritePixel] = None     # cara pixelada pequeña para el muñeco (None = casco)
    retrato: Optional[SpritePixel] = None    # retrato grande 211x211 (20 colores) de la misma foto

    @property
    def personalizado(self):
        return True

    def cabeza(self):
        return self.sprite if self.sprite is not None else super().cabeza()   # polimorfismo

    @staticmethod
    def validar_niveles(niveles):
        niveles = tuple(int(n) for n in niveles)
        if len(niveles) != 4 or any(not NIVEL_MIN <= n <= NIVEL_MAX for n in niveles):
            raise ValueError("Cada estadística debe estar entre 1 y 5")
        if sum(niveles) - 4 * NIVEL_MIN > PUNTOS_LIBRES:
            raise ValueError("Repartiste más puntos de los permitidos")
        return niveles

    def resumen_online(self):
        datos = super().resumen_online()
        if self.retrato is not None:
            datos["retrato"] = self.retrato.a_dict()
        return datos

    @classmethod
    def crear(cls, nombre, color, niveles, sprite=None, retrato=None):
        v, a, m, e = cls.validar_niveles(niveles)
        nombre = (nombre or "TU PILOTO").strip().upper()[:10]
        return cls(
            nombre=nombre, apodo="PILOTO PERSONALIZADO",
            descripcion="Creado por ti: tu cara, tu color y tus puntos.",
            color_auto=tuple(color), color_franja=(250, 250, 250), color_casco=tuple(color),
            color_visor=(255, 214, 64),
            velocidad_max=250 + (v - 1) * 15, aceleracion=135 + (a - 1) * 19,
            manejo=105 + (m - 1) * 21, eficiencia=round(1.25 - (e - 1) * 0.14, 3),
            niveles=(v, a, m, e), sprite=sprite, retrato=retrato)

    def a_dict(self):
        return {"nombre": self.nombre, "color": "#%02x%02x%02x" % self.color_auto,
                "niveles": list(self.niveles), "sprite": self.sprite.a_dict() if self.sprite else None,
                "retrato": self.retrato.a_dict() if self.retrato else None}

    @classmethod
    def desde_dict(cls, d):
        sprite = SpritePixel.desde_dict(d["sprite"]) if d.get("sprite") else None
        retrato = SpritePixel.desde_dict(d["retrato"]) if d.get("retrato") else None
        return cls.crear(d["nombre"], color_desde_hex(d["color"]), d["niveles"], sprite, retrato)


PERSONAJES = (
    Personaje("Rojolio", "LA FLECHA ROJA",
              "Lo más rápido en recta, pero gira re-lento.",
              (226, 52, 52), (255, 230, 90), (226, 52, 52), (255, 210, 80),
              velocidad_max=305, aceleracion=150, manejo=118, eficiencia=1.05),
    Personaje("Brunichi", "EL Man de Azul",
              "Equilibrado en todo.",
              (40, 176, 200), (240, 240, 240), (40, 176, 200), (60, 60, 80),
              velocidad_max=278, aceleracion=170, manejo=150, eficiencia=1.0),
    Personaje("Doña Verde", "LA ECOLÓGICA",
              "Su motor híbrido gasta muchísimo menos gasolina.",
              (70, 190, 90), (250, 250, 210), (70, 190, 90), (120, 230, 255),
              velocidad_max=262, aceleracion=155, manejo=148, eficiencia=0.72),
    Personaje("Ediso", "EL GATO",
              "Hola Ediso.",
              (156, 84, 226), (255, 150, 220), (156, 84, 226), (255, 150, 220),
              velocidad_max=270, aceleracion=205, manejo=186, eficiencia=1.22),
)
