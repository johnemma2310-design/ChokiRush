"""Escena de juego: un nivel de la carrera."""
import copy
import math
import random

import pygame

from . import config as C
from . import ui
from .entidades import (Jugador, Controles, CaraProfe, Gasolina, Escudo, Mancha,
                        TextoFlotante, crear_enemigo, crear_explosion)
from .escena_base import Escena, DialogoProfe, ARRIBA, ABAJO, ACEPTAR
from .fuente_pixel import FUENTE
from .marcador import Marcador
from .pista import NIVELES, Pista


class Carrera(Escena):
    """Un nivel de la carrera. También funciona como 'mundo' para las entidades."""

    OPCIONES_PAUSA = ("CONTINUAR", "REINICIAR NIVEL", "MENÚ PRINCIPAL")

    def __init__(self, juego, personaje, dificultad, indice_nivel=0, marcador=None):
        super().__init__(juego)
        self._personaje = personaje
        self._dificultad = dificultad
        self._indice = indice_nivel
        self._nivel = NIVELES[indice_nivel]
        self._marcador = marcador if marcador is not None else Marcador(dificultad.factor_puntos)
        self._marcador_inicio = copy.deepcopy(self._marcador)
        self._pista = Pista(self._nivel, C.ANCHO_AREA, juego.recursos)
        self._jugador = Jugador(personaje, juego.recursos.auto_jugador(personaje),
                                self._pista.centro(0), 0.0,
                                factor_consumo=dificultad.factor_consumo,
                                costo_choque=dificultad.costo_choque)
        self._enemigos, self._objetos, self._efectos = [], [], []
        self._rng = random.Random()
        self._controles = Controles()
        self._estado = 'cuenta'
        self._t_estado = 3.0
        self._ultimo_segundo = 4
        self._t_ya = 0.0
        self._t = 0.0
        self._bono = 0.0
        self._pausa = False
        self._sel_pausa = 0
        self._sacudida = 0.0
        self._t_alarma = 0.0
        n = self._nivel
        self._proximo = {
            'auto': 0.0, 'cara': 0.0, 'gas': 1500.0,
            'escudo': self._rng.uniform(*n.intervalo_escudo),
            'mancha': n.intervalo_manchas[0] if n.intervalo_manchas else float('inf'),
        }
        self._area = pygame.Surface((C.ANCHO_AREA, C.ALTO))
        # el profe explica lo básico antes de la primera carrera (solo la primera vez)
        self._tutorial = None
        self._aviso = None
        if indice_nivel == 0 and not juego.almacen.leer("tutorial_carrera", False):
            self._estado = 'tutorial'
            self._tutorial = DialogoProfe(juego.recursos, juego.audio, (
                "¡A CORRER! MANTÉN ARRIBA PARA ACELERAR Y GIRA CON LAS FLECHAS.",
                "ATRAPA MIS MONEDAS Y CUIDA LA GASOLINA. ¡NO TE SALGAS DE LA PISTA!",
                "CUANDO ESTÉS LISTO, DALE ENTER. ¡SUERTE!",
            ), rect=(4, 150, C.ANCHO_AREA - 8, 86))

    def _avisar(self, clave, texto):
        """El profe comenta algo durante la carrera sin pausar el juego (una vez por partida)."""
        if clave in self.juego.avisos_vistos:
            return
        self.juego.avisos_vistos.add(clave)
        self._aviso = DialogoProfe(self.juego.recursos, self.juego.audio, (texto,),
                                   rect=(4, 172, C.ANCHO_AREA - 8, 62), automatico=True, pausa=2.5)

    def _terminar_tutorial(self):
        self._tutorial = None
        self._estado = 'cuenta'
        self.juego.almacen.escribir("tutorial_carrera", True)

    # ---------- interfaz de "mundo" para las entidades ----------
    @property
    def pista(self):
        return self._pista

    @property
    def jugador(self):
        return self._jugador

    @property
    def marcador(self):
        return self._marcador

    @property
    def controles(self):
        return self._controles

    @property
    def camara(self):
        return self._jugador.y

    def sonido(self, nombre):
        self.juego.audio.efecto(nombre)

    def texto_flotante(self, x, y, texto, color):
        self._efectos.append(TextoFlotante(x, y, texto, color))

    def destellos(self, x, y, color):
        self._efectos.extend(crear_explosion(x, y, self._rng, colores=(color, C.BLANCO), cantidad=10, fuerza=60))

    # ---------- ciclo de vida ----------
    def al_entrar(self):
        self.juego.audio.musica(None)

    def manejar_evento(self, ev):
        if ev.type != pygame.KEYDOWN:
            return
        audio = self.juego.audio
        if self._estado == 'tutorial':
            if ev.key == pygame.K_ESCAPE:
                self._terminar_tutorial()
            elif ev.key in ACEPTAR:
                audio.efecto('ok')
                if not self._tutorial.avanzar():
                    self._terminar_tutorial()
            return
        if self._pausa:
            if ev.key in (pygame.K_ESCAPE, pygame.K_p):
                self._reanudar()
            elif ev.key in ARRIBA:
                self._sel_pausa = (self._sel_pausa - 1) % len(self.OPCIONES_PAUSA)
                audio.efecto('mover')
            elif ev.key in ABAJO:
                self._sel_pausa = (self._sel_pausa + 1) % len(self.OPCIONES_PAUSA)
                audio.efecto('mover')
            elif ev.key in ACEPTAR:
                audio.efecto('ok')
                if self._sel_pausa == 0:
                    self._reanudar()
                elif self._sel_pausa == 1:
                    self.juego.cambiar_escena(Carrera(self.juego, self._personaje, self._dificultad,
                                                      self._indice, copy.deepcopy(self._marcador_inicio)))
                else:
                    from .escenas import MenuPrincipal
                    self.juego.cambiar_escena(MenuPrincipal(self.juego))
            return
        if ev.key in (pygame.K_ESCAPE, pygame.K_p) and self._estado in ('cuenta', 'corriendo'):
            self._pausa = True
            self._sel_pausa = 0
            audio.pausar()
            audio.efecto('mover')

    def _reanudar(self):
        self._pausa = False
        self.juego.audio.reanudar()

    def _leer_controles(self):
        k = pygame.key.get_pressed()
        derecha = k[pygame.K_RIGHT] or k[pygame.K_d]
        izquierda = k[pygame.K_LEFT] or k[pygame.K_a]
        return Controles(acelerar=bool(k[pygame.K_UP] or k[pygame.K_w] or k[pygame.K_z]),
                         frenar=bool(k[pygame.K_DOWN] or k[pygame.K_s] or k[pygame.K_x]),
                         direccion=int(bool(derecha)) - int(bool(izquierda)))

    def actualizar(self, dt):
        if self._pausa:
            return
        if self._estado == 'tutorial':
            self._t += dt
            self._tutorial.actualizar(dt)
            return
        if self._aviso is not None:
            self._aviso.actualizar(dt)
            if not self._aviso.activo:
                self._aviso = None
        self._t += dt
        self._t_ya = max(0.0, self._t_ya - dt)
        self._sacudida = max(0.0, self._sacudida - dt)
        self._marcador.actualizar(dt)
        j = self._jugador

        if self._estado == 'cuenta':
            self._controles = Controles()
            self._t_estado -= dt
            segundo = math.ceil(self._t_estado)
            if segundo != self._ultimo_segundo and segundo > 0:
                self._ultimo_segundo = segundo
                self.sonido('cuenta')
            if self._t_estado <= 0:
                self._estado = 'corriendo'
                self._t_ya = 0.9
                self.sonido('ya')
                self.juego.audio.musica('carrera')
        elif self._estado == 'corriendo':
            self._controles = self._leer_controles()
        elif self._estado == 'meta':
            centro = self._pista.centro(j.y)
            giro = 0 if abs(centro - j.x) < 3 else (1 if centro > j.x else -1)
            self._controles = Controles(acelerar=True, direccion=giro)
        else:
            self._controles = Controles()

        y_antes = j.y
        j.actualizar(dt, self)
        if self._estado == 'corriendo':
            self._marcador.avanzar(j.y - y_antes)

        for e in self._enemigos:
            e.actualizar(dt, self)
        for o in self._objetos:
            o.actualizar(dt, self)
        for f in self._efectos:
            f.actualizar(dt)

        if self._estado == 'corriendo':
            self._generar()
            self._colisiones()
            self._alarma_gasolina(dt)
            if j.y >= self._nivel.longitud:
                self._estado = 'meta'
                self._t_estado = 3.0
                self.juego.audio.jingle('nivel')
            elif j.sin_gasolina and j.velocidad <= 0.5 and j.estado != Jugador.CHOCADO:
                self._estado = 'sin_gasolina'
                self._t_estado = 2.5
                self.juego.audio.jingle('perder')
        elif self._estado == 'meta':
            self._t_estado -= dt
            if j.gasolina > 0:
                q = min(j.gasolina, 45 * dt)
                j.gastar(q)
                self._bono += self._marcador.sumar(q * C.PUNTOS_BONO_GAS)
            elif self._t_estado <= 0:
                self._siguiente_nivel()
        elif self._estado == 'sin_gasolina':
            self._t_estado -= dt
            if self._t_estado <= 0:
                from .escenas import FinPartida
                self.juego.cambiar_escena(FinPartida(self.juego, False, self._marcador, self._personaje,
                                                     self._nivel.numero, self._dificultad))

        self._enemigos = [e for e in self._enemigos if e.activo]
        self._objetos = [o for o in self._objetos if o.activo]
        self._efectos = [f for f in self._efectos if f.vivo]

    def _siguiente_nivel(self):
        if self._indice + 1 < len(NIVELES):
            self.juego.cambiar_escena(Carrera(self.juego, self._personaje, self._dificultad,
                                              self._indice + 1, self._marcador))
        else:
            from .escenas import FinPartida
            self.juego.cambiar_escena(FinPartida(self.juego, True, self._marcador, self._personaje,
                                                 len(NIVELES), self._dificultad))

    def _alarma_gasolina(self, dt):
        if self._jugador.fraccion_gasolina < 0.3:
            self._avisar("gasolina", "¡TE QUEDA POCA GASOLINA! BUSCA UN BIDÓN ROJO.")
        if self._marcador.combo >= 3:
            self._avisar("combo", "¡ESO! SIGUE ATRAPANDO MIS CARAS PARA EL COMBO.")
        if self._jugador.fraccion_gasolina < 0.2:
            self._t_alarma -= dt
            if self._t_alarma <= 0:
                self._t_alarma = 1.4
                self.sonido('alarma')

    # ---------- generación de tráfico y objetos ----------
    def _hueco_libre(self, y, ancho_obj):
        centro = self._pista.centro(y)
        mitad = self._pista.ancho(y) / 2 - ancho_obj / 2 - 6
        for _ in range(8):
            desp = self._rng.uniform(-mitad, mitad)
            x = centro + desp
            if all(abs(o.y - y) > 30 or abs(o.x - x) > 22 for o in self._enemigos + self._objetos):
                return desp
        return None

    def _generar(self):
        j, n, rng, rec = self._jugador, self._nivel, self._rng, self.juego.recursos
        frente = j.y + C.JUGADOR_Y + 40
        if frente > n.longitud - 80:
            return
        p = self._proximo
        if frente >= p['auto']:
            tipos, pesos = zip(*n.enemigos)
            tipo = rng.choices(tipos, pesos)[0]
            desp = self._hueco_libre(frente, 14)
            if desp is not None:
                enemigo = crear_enemigo(tipo, desp, frente, rec, rng)
                enemigo.escalar_velocidad(self._dificultad.factor_vel_enemigos)
                enemigo.actualizar(0, self)
                self._enemigos.append(enemigo)
            p['auto'] = frente + n.distancia_trafico * self._dificultad.factor_trafico * rng.uniform(0.6, 1.4)
        if frente >= p['cara']:
            desp = self._hueco_libre(frente, 22)
            if desp is not None:
                filas = 3 if rng.random() < 0.3 else 1
                for i in range(filas):
                    yy = frente + i * 28
                    self._objetos.append(CaraProfe(self._pista.centro(yy) + desp, yy, rec.cara_profe))
            p['cara'] = frente + rng.uniform(260, 520)
        if frente >= p['gas']:
            self._colocar(Gasolina, rec.gasolina(), frente)
            p['gas'] = frente + rng.uniform(1700, 2500)
        if frente >= p['escudo']:
            self._colocar(Escudo, rec.escudo(), frente)
            p['escudo'] = frente + rng.uniform(*n.intervalo_escudo)
        if n.intervalo_manchas and frente >= p['mancha']:
            self._colocar(Mancha, rec.mancha(n.tema), frente)
            p['mancha'] = frente + rng.uniform(*n.intervalo_manchas) * self._dificultad.factor_trafico

    def _colocar(self, clase, sprite, y):
        desp = self._hueco_libre(y, sprite.get_width())
        if desp is not None:
            self._objetos.append(clase(self._pista.centro(y) + desp, y, sprite))

    # ---------- colisiones ----------
    def _colisiones(self):
        j = self._jugador
        if j.estado == Jugador.CHOCADO:
            return
        caja = j.hitbox()
        izq, der = self._pista.limites(j.y)
        if caja.left < izq or caja.right > der:
            if j.puede_chocar:
                self._chocar("¡FUERA DE PISTA!")
                return
            j.limitar_a(izq, der)

        for e in self._enemigos:
            if not e.adelantado and e.y < j.y - 16:
                e.adelantado = True
                self._marcador.registrar_adelanto(C.PUNTOS_ADELANTO)
            if e.activo and caja.colliderect(e.hitbox()):
                if j.tiene_escudo:
                    e.desactivar()
                    ganados = self._marcador.sumar(C.PUNTOS_DESTRUIR)
                    self._efectos.extend(crear_explosion(e.x, e.y, self._rng))
                    self.texto_flotante(e.x, e.y, f"+{int(ganados)}", C.CIAN)
                    self.sonido('destruir')
                    self._sacudida = 0.15
                elif j.puede_chocar:
                    self._chocar("¡CRASH!")
                    return

        for o in self._objetos:
            if o.activo and caja.colliderect(o.hitbox()):
                o.interactuar(j, self)

    def _chocar(self, mensaje):
        j = self._jugador
        if j.chocar():
            self._efectos.extend(crear_explosion(j.x, j.y, self._rng, cantidad=34, fuerza=110))
            self.texto_flotante(j.x, j.y + 10, mensaje, C.ROJO)
            self._sacudida = 0.4
            self.sonido('choque')
            self._avisar("choque", "¡AUCH! CADA CHOQUE TE QUITA GASOLINA. ¡CON CUIDADO!")

    # ---------- dibujo ----------
    def dibujar(self, sup):
        area, cam = self._area, self.camara
        self._pista.dibujar(area, cam)
        for o in self._objetos:
            o.dibujar(area, cam)
        for e in self._enemigos:
            e.dibujar(area, cam)
        self._jugador.dibujar(area, cam)
        for f in self._efectos:
            f.dibujar(area, cam)
        if self._estado == 'tutorial':
            ui.velo(area, 110)
            ui.panel(area, (20, 34, 200, 36))
            FUENTE.texto(area, f"NIVEL {self._nivel.numero}", C.ANCHO_AREA // 2, 42, color=C.AMARILLO, alinear='centro')
            FUENTE.texto(area, self._nivel.nombre, C.ANCHO_AREA // 2, 55, color=C.BLANCO, alinear='centro')
            self._tutorial.dibujar(area)
        else:
            self._dibujar_avisos(area)
            if self._aviso is not None:
                self._aviso.dibujar(area)

        sup.fill(C.NEGRO)
        dx = dy = 0
        if self._sacudida > 0:
            dx, dy = self._rng.randint(-2, 2), self._rng.randint(-2, 2)
        sup.blit(area, (dx, dy))
        self._dibujar_hud(sup)
        if self._pausa:
            self._dibujar_pausa(sup)

    def _dibujar_avisos(self, area):
        cx = C.ANCHO_AREA // 2
        if self._estado == 'cuenta':
            ui.panel(area, (20, 34, 200, 36))
            FUENTE.texto(area, f"NIVEL {self._nivel.numero}", cx, 42, color=C.AMARILLO, alinear='centro')
            FUENTE.texto(area, self._nivel.nombre, cx, 55, color=C.BLANCO, alinear='centro')
            FUENTE.texto(area, str(max(1, math.ceil(self._t_estado))), cx, 92, escala=6,
                         color=C.BLANCO, sombra=(120, 30, 30), alinear='centro')
        if self._t_ya > 0:
            FUENTE.texto(area, "¡YA!", cx, 92, escala=5, color=C.VERDE, sombra=(20, 80, 30), alinear='centro')
        if self._estado == 'corriendo' and self._jugador.fraccion_gasolina < 0.2 and int(self._t * 3) % 2:
            FUENTE.texto(area, "¡GASOLINA BAJA!", cx, 6, color=C.ROJO, alinear='centro')
        if self._estado == 'meta':
            ui.panel(area, (20, 60, 200, 70))
            FUENTE.texto(area, "¡META!", cx, 70, escala=3, color=C.AMARILLO, alinear='centro')
            FUENTE.texto(area, "NIVEL COMPLETADO", cx, 98, color=C.BLANCO, alinear='centro')
            FUENTE.texto(area, f"BONO GASOLINA +{int(self._bono)}", cx, 112, color=C.VERDE, alinear='centro')
        if self._estado == 'sin_gasolina':
            ui.panel(area, (20, 70, 200, 40), borde=C.ROJO)
            FUENTE.texto(area, "¡SIN GASOLINA!", cx, 84, escala=2, color=C.ROJO, alinear='centro')

    def _dibujar_hud(self, sup):
        x0 = C.ANCHO_AREA
        sup.fill(C.FONDO_HUD, (x0, 0, C.ANCHO - x0, C.ALTO))
        sup.fill((60, 52, 96), (x0, 0, 1, C.ALTO))
        x = x0 + 7
        j, m = self._jugador, self._marcador

        FUENTE.texto(sup, "PUNTOS", x, 6, color=C.GRIS)
        FUENTE.texto(sup, f"{m.puntos:06d}", x, 15, color=C.BLANCO)
        FUENTE.texto(sup, "RÉCORD", x, 29, color=C.GRIS)
        FUENTE.texto(sup, f"{max(m.puntos, self.juego.records.mejor):06d}", x, 38, color=C.AMARILLO)
        FUENTE.texto(sup, f"NIVEL {self._nivel.numero}/{len(NIVELES)}", x, 52, color=C.CIAN)

        FUENTE.texto(sup, "GASOLINA", x, 66, color=C.GRIS)
        frac = j.fraccion_gasolina
        color = C.VERDE if frac > 0.5 else (C.AMARILLO if frac > 0.2 else C.ROJO)
        if frac <= 0.2 and int(self._t * 6) % 2:
            color = C.BLANCO
        ui.barra(sup, (x, 75, 66, 8), frac, color, segmentos=5)

        FUENTE.texto(sup, "VELOCIDAD", x, 90, color=C.GRIS)
        FUENTE.texto(sup, f"{j.km_h:3d} KM/H", x, 99, color=C.BLANCO)

        # progreso vertical
        FUENTE.texto(sup, "RUTA", x, 114, color=C.GRIS)
        top, bot = 126, 200
        pygame.draw.rect(sup, (44, 40, 64), (x + 2, top, 6, bot - top))
        progreso = max(0.0, min(1.0, j.y / self._nivel.longitud))
        alto = int((bot - top - 2) * progreso)
        sup.fill(j.personaje.color_auto, (x + 3, bot - 1 - alto, 4, alto))
        for i in range(4):                               # bandera a cuadros
            for k in range(3):
                c = C.BLANCO if (i + k) % 2 else C.NEGRO
                sup.fill(c, (x + 30 + k * 3, 113 + i * 2, 3, 2))
        yy = bot - 1 - alto
        sup.fill(C.BLANCO, (x + 1, yy - 1, 8, 2))

        # caras recogidas y combo
        sup.blit(self.juego.recursos.cara_profe, (x + 22, 126))
        FUENTE.texto(sup, f"X{m.caras}", x + 22, 156, color=C.AMARILLO)
        if m.combo_activo:
            FUENTE.texto(sup, f"COMBO", x + 22, 166, color=C.NARANJA)
            FUENTE.texto(sup, f"X{m.combo}", x + 22, 176, escala=2, color=C.NARANJA)
            ui.barra(sup, (x + 22, 192, 40, 4), m.fraccion_combo, C.NARANJA)

        base = self.juego.recursos.retrato(j.personaje)
        retrato = self.juego.recursos.escalar(base, 2 if base.get_height() <= 16 else 1)
        sup.blit(retrato, (x, C.ALTO - 3 - retrato.get_height()))
        FUENTE.texto(sup, self._dificultad.nombre, C.ANCHO - 4, C.ALTO - 10, color=self._dificultad.color,
                     alinear='der')
        if j.tiene_escudo:
            sup.blit(self.juego.recursos.escudo(), (x + 34, 210))
            FUENTE.texto(sup, f"{math.ceil(j.tiempo_escudo)}", x + 50, 213, color=C.CIAN)

    def _dibujar_pausa(self, sup):
        ui.velo(sup, 160)
        ui.panel(sup, (80, 70, 160, 100))
        FUENTE.texto(sup, "PAUSA", 160, 80, escala=3, color=C.AMARILLO, alinear='centro')
        for i, op in enumerate(self.OPCIONES_PAUSA):
            color = C.AMARILLO if i == self._sel_pausa else C.GRIS
            texto = f"> {op} <" if i == self._sel_pausa else op
            FUENTE.texto(sup, texto, 160, 112 + i * 14, color=color, alinear='centro')
