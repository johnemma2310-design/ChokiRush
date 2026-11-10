"""Entidades del mundo: vehículos, objetos interactivos y efectos visuales.

Jerarquía principal:
    Entidad (abstracta)
    ├── Vehiculo
    │   ├── Jugador
    │   └── Enemigo (abstracta)  -> AutoCivil, AutoZigzag, Camion, AutoRival
    └── Interactivo (abstracta)
        ├── Coleccionable (abstracta) -> CaraProfe, Gasolina, Escudo
        └── Obstaculo (abstracta)     -> Mancha
    Efecto (abstracta) -> Particula, TextoFlotante

Coordenadas de mundo: `x` en pixeles de pantalla; `y` = distancia recorrida (crece hacia adelante).
"""
import math
import random
from abc import ABC, abstractmethod
from dataclasses import dataclass

import pygame

from . import config as C
from .fuente_pixel import FUENTE


@dataclass
class Controles:
    acelerar: bool = False
    frenar: bool = False
    direccion: int = 0          # -1 izquierda, 0 recto, 1 derecha


# =====================================================================
#  Base
# =====================================================================
class Entidad(ABC):
    def __init__(self, x, y, sprite, margen=2):
        self._x = float(x)
        self._y = float(y)
        self._sprite = sprite
        self._margen = margen
        self._activo = True

    @property
    def x(self):
        return self._x

    @property
    def y(self):
        return self._y

    @property
    def activo(self):
        return self._activo

    @property
    def ancho(self):
        return self._sprite.get_width()

    @property
    def alto(self):
        return self._sprite.get_height()

    def desactivar(self):
        self._activo = False

    def hitbox(self):
        m = self._margen
        return pygame.Rect(int(self._x - self.ancho / 2 + m), int(self._y - self.alto / 2 + m),
                           max(1, self.ancho - 2 * m), max(1, self.alto - 2 * m))

    @staticmethod
    def a_pantalla(y_mundo, camara):
        return C.JUGADOR_Y - (y_mundo - camara)

    def en_pantalla_y(self, camara):
        return self.a_pantalla(self._y, camara)

    @abstractmethod
    def actualizar(self, dt, mundo):
        """Cada entidad decide cómo evoluciona en el tiempo (polimorfismo)."""

    def _sprite_actual(self):
        return self._sprite

    def dibujar(self, sup, camara):
        sy = self.en_pantalla_y(camara)
        if sy < -40 or sy > C.ALTO + 40:
            return
        spr = self._sprite_actual()
        sup.blit(spr, (round(self._x - spr.get_width() / 2), round(sy - spr.get_height() / 2)))


class Vehiculo(Entidad):
    def __init__(self, x, y, sprite, velocidad, margen=2):
        super().__init__(x, y, sprite, margen)
        self._velocidad = float(velocidad)

    @property
    def velocidad(self):
        return self._velocidad

    def _avanzar(self, dt):
        self._y += self._velocidad * dt


# =====================================================================
#  Jugador
# =====================================================================
class Jugador(Vehiculo):
    NORMAL = "normal"
    DERRAPANDO = "derrapando"
    CHOCADO = "chocado"

    T_CHOQUE = 1.3
    T_INVULNERABLE = 2.0
    T_DERRAPE = 0.9

    def __init__(self, personaje, sprite, x, y, factor_consumo=1.0, costo_choque=C.COSTO_CHOQUE):
        super().__init__(x, y, sprite, 0.0, margen=2)
        self._personaje = personaje
        self._factor_consumo = factor_consumo
        self._costo_choque = costo_choque
        self._gasolina = C.GASOLINA_MAX
        self._estado = self.NORMAL
        self._t_estado = 0.0
        self._t_invulnerable = 0.0
        self._t_escudo = 0.0
        self._t_espera_derrape = 0.0
        self._dir_derrape = 1
        self._angulo = 0.0
        self._reloj = 0.0

    # ---- consultas ----
    @property
    def personaje(self):
        return self._personaje

    @property
    def gasolina(self):
        return self._gasolina

    @property
    def fraccion_gasolina(self):
        return self._gasolina / C.GASOLINA_MAX

    @property
    def sin_gasolina(self):
        return self._gasolina <= 0

    @property
    def estado(self):
        return self._estado

    @property
    def km_h(self):
        return int(self._velocidad * 0.9)

    @property
    def tiene_escudo(self):
        return self._t_escudo > 0

    @property
    def tiempo_escudo(self):
        return self._t_escudo

    @property
    def puede_chocar(self):
        return self._estado != self.CHOCADO and self._t_invulnerable <= 0 and self._t_escudo <= 0

    # ---- comandos (única forma de modificar el estado) ----
    def recargar(self, cantidad):
        self._gasolina = min(C.GASOLINA_MAX, self._gasolina + max(0.0, cantidad))

    def gastar(self, cantidad):
        self._gasolina = max(0.0, self._gasolina - max(0.0, cantidad))

    def activar_escudo(self, segundos):
        self._t_escudo = max(self._t_escudo, segundos)

    def chocar(self):
        if not self.puede_chocar:
            return False
        self._estado = self.CHOCADO
        self._t_estado = self.T_CHOQUE
        self._velocidad = 0.0
        self._angulo = 0.0
        self.gastar(self._costo_choque)
        return True

    def derrapar(self):
        if (self._estado != self.NORMAL or self._t_espera_derrape > 0
                or self._t_escudo > 0 or self._velocidad < 40):
            return False
        self._estado = self.DERRAPANDO
        self._t_estado = self.T_DERRAPE
        self._t_espera_derrape = 1.6
        self._dir_derrape = random.choice((-1, 1))
        return True

    def limitar_a(self, izq, der):
        medio = self.ancho / 2 - self._margen
        self._x = max(izq + medio, min(der - medio, self._x))

    # ---- ciclo ----
    def actualizar(self, dt, mundo):
        self._reloj += dt
        self._t_invulnerable = max(0.0, self._t_invulnerable - dt)
        self._t_escudo = max(0.0, self._t_escudo - dt)
        self._t_espera_derrape = max(0.0, self._t_espera_derrape - dt)

        if self._estado == self.CHOCADO:
            self._t_estado -= dt
            if self._t_estado <= 0:
                self._x = mundo.pista.centro(self._y)
                self._estado = self.NORMAL
                self._t_invulnerable = self.T_INVULNERABLE
            return

        controles = mundo.controles
        if self._estado == self.DERRAPANDO:
            self._t_estado -= dt
            self._angulo = (self._angulo + 760 * dt * self._dir_derrape) % 360
            self._x += self._dir_derrape * 62 * dt
            self._velocidad = max(0.0, self._velocidad - 90 * dt)
            if self._t_estado <= 0:
                self._estado = self.NORMAL
                self._angulo = 0.0
        else:
            self._conducir(dt, controles)
        self._consumir(dt, controles)
        self._avanzar(dt)

    def _conducir(self, dt, ctrl):
        p = self._personaje
        if ctrl.acelerar and not self.sin_gasolina:
            self._velocidad += p.aceleracion * dt
        elif ctrl.frenar:
            self._velocidad -= 340 * dt
        else:
            self._velocidad -= 50 * dt
        if self.sin_gasolina:
            self._velocidad -= 80 * dt
        self._velocidad = max(0.0, min(p.velocidad_max, self._velocidad))
        agarre = min(1.0, self._velocidad / 90)
        self._x += ctrl.direccion * p.manejo * agarre * dt

    def _consumir(self, dt, ctrl):
        p = self._personaje
        if self._velocidad > 0 or ctrl.acelerar:
            carga = 0.3 + 0.7 * self._velocidad / p.velocidad_max
            self.gastar(C.CONSUMO_BASE * p.eficiencia * self._factor_consumo * carga * dt)

    def _sprite_actual(self):
        if self._angulo:
            return pygame.transform.rotate(self._sprite, self._angulo)
        return self._sprite

    def dibujar(self, sup, camara):
        if self._estado == self.CHOCADO:
            return
        if self._t_invulnerable > 0 and int(self._reloj * 14) % 2 == 0:
            return
        super().dibujar(sup, camara)
        if self._t_escudo > 0 and (self._t_escudo > 1.5 or int(self._reloj * 10) % 2):
            color = C.CIAN if int(self._reloj * 8) % 2 else C.BLANCO
            pygame.draw.circle(sup, color, (round(self._x), round(self.en_pantalla_y(camara))), 13, 1)


# =====================================================================
#  Enemigos
# =====================================================================
class Enemigo(Vehiculo):
    """Vehículo de tráfico. Sigue la carretera usando un desplazamiento respecto al centro."""

    def __init__(self, desplazamiento, y, sprite, velocidad, margen=2):
        super().__init__(0, y, sprite, velocidad, margen)
        self._desp = float(desplazamiento)
        self._t = 0.0
        self.adelantado = False

    def escalar_velocidad(self, factor):
        self._velocidad *= max(0.1, factor)

    @classmethod
    @abstractmethod
    def crear(cls, desplazamiento, y, recursos, rng):
        """Método fábrica: cada tipo sabe cómo construirse."""

    @abstractmethod
    def _comportamiento(self, dt, mundo):
        """Lo que hace distinto a cada tipo de enemigo."""

    def actualizar(self, dt, mundo):
        self._t += dt
        self._comportamiento(dt, mundo)
        self._avanzar(dt)
        pista = mundo.pista
        limite = pista.ancho(self._y) / 2 - self.ancho / 2 - 3
        self._desp = max(-limite, min(limite, self._desp))
        self._x = pista.centro(self._y) + self._desp
        sy = self.en_pantalla_y(mundo.camara)
        if sy > C.ALTO + 60 or sy < -200:
            self.desactivar()


class AutoCivil(Enemigo):
    """Conduce recto por su carril."""
    COLORES = ((240, 200, 40), (232, 232, 232), (190, 122, 62), (150, 150, 162))

    @classmethod
    def crear(cls, desplazamiento, y, recursos, rng):
        return cls(desplazamiento, y, recursos.auto(rng.choice(cls.COLORES)), rng.uniform(110, 160))

    def _comportamiento(self, dt, mundo):
        pass


class AutoZigzag(Enemigo):
    """Va de lado a lado como si estuviera distraído con el celular."""

    def __init__(self, desplazamiento, y, sprite, velocidad, fase):
        super().__init__(desplazamiento, y, sprite, velocidad)
        self._base = desplazamiento
        self._fase = fase

    @classmethod
    def crear(cls, desplazamiento, y, recursos, rng):
        return cls(desplazamiento, y, recursos.auto((250, 110, 180), (255, 255, 255)),
                   rng.uniform(120, 150), rng.uniform(0, math.tau))

    def _comportamiento(self, dt, mundo):
        self._desp = self._base + math.sin(self._t * 2.4 + self._fase) * 24


class Camion(Enemigo):
    """Grande y lento: un muro rodante."""
    CABINAS = ((230, 130, 40), (60, 140, 200), (200, 60, 60))

    @classmethod
    def crear(cls, desplazamiento, y, recursos, rng):
        sprite = recursos.camion(rng.choice(cls.CABINAS), (175, 175, 182))
        return cls(desplazamiento, y, sprite, rng.uniform(90, 115))

    def _comportamiento(self, dt, mundo):
        pass


class AutoRival(Enemigo):
    """IA sencilla: cuando el jugador se acerca por detrás, se le cierra en el camino."""

    @classmethod
    def crear(cls, desplazamiento, y, recursos, rng):
        return cls(desplazamiento, y, recursos.auto((40, 70, 220), (255, 214, 64)), rng.uniform(140, 185))

    def _comportamiento(self, dt, mundo):
        j = mundo.jugador
        distancia = self._y - j.y
        if 0 < distancia < 150 and j.estado != Jugador.CHOCADO:
            objetivo = j.x - mundo.pista.centro(self._y)
            paso = 55 * dt
            if abs(objetivo - self._desp) > paso:
                self._desp += paso if objetivo > self._desp else -paso


FABRICA_ENEMIGOS = {'civil': AutoCivil, 'zigzag': AutoZigzag, 'camion': Camion, 'rival': AutoRival}


def crear_enemigo(tipo, desplazamiento, y, recursos, rng):
    return FABRICA_ENEMIGOS[tipo].crear(desplazamiento, y, recursos, rng)


# =====================================================================
#  Objetos interactivos
# =====================================================================
class Interactivo(Entidad):
    """Algo con lo que el jugador puede tocarse. Cada subclase define qué pasa."""

    def __init__(self, x, y, sprite, margen=1):
        super().__init__(x, y, sprite, margen)
        self._t = random.uniform(0, math.tau)

    def actualizar(self, dt, mundo):
        self._t += dt
        if self.en_pantalla_y(mundo.camara) > C.ALTO + 40:
            self.desactivar()

    @abstractmethod
    def interactuar(self, jugador, mundo):
        """Reacción al contacto con el jugador (polimorfismo)."""


class Coleccionable(Interactivo):
    """Se recoge una sola vez y desaparece."""

    def interactuar(self, jugador, mundo):
        if not self.activo or jugador.estado == Jugador.CHOCADO:
            return
        self._aplicar(jugador, mundo)
        self.desactivar()

    @abstractmethod
    def _aplicar(self, jugador, mundo):
        """Efecto concreto al recogerlo."""

    def dibujar(self, sup, camara):
        sy = self.en_pantalla_y(camara) + math.sin(self._t * 4) * 1.5
        if -30 < sy < C.ALTO + 30:
            spr = self._sprite
            sup.blit(spr, (round(self._x - spr.get_width() / 2), round(sy - spr.get_height() / 2)))


class CaraProfe(Coleccionable):
    def _aplicar(self, jugador, mundo):
        ganados = mundo.marcador.recoger_cara(C.PUNTOS_CARA)
        combo = mundo.marcador.combo
        texto = f"+{ganados}" if combo == 1 else f"+{ganados} X{combo}"
        mundo.texto_flotante(self._x, self._y, texto, C.AMARILLO)
        mundo.destellos(self._x, self._y, C.AMARILLO)
        mundo.sonido('moneda')


class Gasolina(Coleccionable):
    def _aplicar(self, jugador, mundo):
        jugador.recargar(C.GAS_RECARGA)
        mundo.texto_flotante(self._x, self._y, "+GASOLINA", C.VERDE)
        mundo.destellos(self._x, self._y, C.VERDE)
        mundo.sonido('gasolina')


class Escudo(Coleccionable):
    def _aplicar(self, jugador, mundo):
        jugador.activar_escudo(C.T_ESCUDO)
        mundo.texto_flotante(self._x, self._y, "¡ESCUDO!", C.CIAN)
        mundo.destellos(self._x, self._y, C.CIAN)
        mundo.sonido('escudo')


class Obstaculo(Interactivo):
    """Permanece en la pista después del contacto."""


class Mancha(Obstaculo):
    """Aceite (o hielo en la nieve): hace derrapar al jugador."""

    def interactuar(self, jugador, mundo):
        if jugador.derrapar():
            mundo.sonido('derrape')
            mundo.texto_flotante(self._x, self._y, "¡DERRAPE!", C.NARANJA)


# =====================================================================
#  Efectos visuales
# =====================================================================
class Efecto(ABC):
    def __init__(self, x, y, vida):
        self._x = float(x)
        self._y = float(y)
        self._vida = vida
        self._edad = 0.0

    @property
    def vivo(self):
        return self._edad < self._vida

    def actualizar(self, dt):
        self._edad += dt
        self._mover(dt)

    @abstractmethod
    def _mover(self, dt):
        pass

    @abstractmethod
    def dibujar(self, sup, camara):
        pass


class Particula(Efecto):
    def __init__(self, x, y, vx, vy, color, vida, tam):
        super().__init__(x, y, vida)
        self._vx, self._vy = vx, vy
        self._color = color
        self._tam = tam

    def _mover(self, dt):
        self._x += self._vx * dt
        self._y += self._vy * dt
        frenado = max(0.0, 1 - 2.5 * dt)
        self._vx *= frenado
        self._vy *= frenado

    def dibujar(self, sup, camara):
        t = max(1, round(self._tam * (1 - self._edad / self._vida)))
        sy = Entidad.a_pantalla(self._y, camara)
        sup.fill(self._color, (round(self._x - t / 2), round(sy - t / 2), t, t))


class TextoFlotante(Efecto):
    def __init__(self, x, y, texto, color, vida=1.1):
        super().__init__(x, y, vida)
        self._texto = texto
        self._color = color

    def _mover(self, dt):
        self._y += 38 * dt

    def dibujar(self, sup, camara):
        if self._edad > self._vida * 0.7 and int(self._edad * 20) % 2:
            return
        mitad = FUENTE.ancho(self._texto) // 2 + 2
        x = max(mitad, min(sup.get_width() - mitad, self._x))
        FUENTE.texto(sup, self._texto, x, Entidad.a_pantalla(self._y, camara) - 14,
                     color=self._color, alinear='centro')


def crear_explosion(x, y, rng, colores=((255, 220, 80), (255, 140, 40), (230, 50, 40), (90, 90, 100)),
                    cantidad=26, fuerza=95):
    particulas = []
    for _ in range(cantidad):
        ang = rng.uniform(0, math.tau)
        v = rng.uniform(0.3, 1.0) * fuerza
        particulas.append(Particula(x, y, math.cos(ang) * v, math.sin(ang) * v, rng.choice(colores),
                                    rng.uniform(0.4, 0.9), rng.choice((2, 3, 4))))
    return particulas
