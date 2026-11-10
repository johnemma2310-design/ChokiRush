"""Escenas de menú: inicio, pilotos, creador, dificultad, ayuda, fin de partida y clasificación."""
import math

import pygame

from . import config as C
from . import ui
from .carrera import Carrera
from .dificultad import DIFICULTADES
from .escena_base import (Escena, FondoAnimado, CampoTexto, Podio, DialogoProfe,
                          ARRIBA, ABAJO, IZQUIERDA, DERECHA, ACEPTAR)
from .fuente_pixel import FUENTE
from .personajes import PERSONAJES, PersonajePersonalizado, PUNTOS_LIBRES, NIVEL_MIN, NIVEL_MAX
from .pista import NIVELES
from .pixelador import Pixelador, color_desde_hex
from .plataforma import ES_WEB


# =====================================================================
#  Menú principal
# =====================================================================
class MenuPrincipal(Escena):
    def __init__(self, juego):
        super().__init__(juego)
        self._fondo = FondoAnimado(juego)
        self._sel = 0
        self._t = 0.0
        self._opciones = [("JUGAR", lambda: SeleccionPiloto(self.juego)),
                          ("CREAR PILOTO", lambda: CreadorPiloto(self.juego, self.juego.piloto_personalizado)),
                          ("CLASIFICACIÓN", lambda: Clasificacion(self.juego)),
                          ("CÓMO JUGAR", lambda: ComoJugar(self.juego))]
        if not ES_WEB:
            self._opciones.append(("SALIR", None))

    def al_entrar(self):
        self.juego.audio.musica('menu')

    def manejar_evento(self, ev):
        if ev.type != pygame.KEYDOWN:
            return
        n = len(self._opciones)
        if ev.key in ARRIBA:
            self._sel = (self._sel - 1) % n
            self.juego.audio.efecto('mover')
        elif ev.key in ABAJO:
            self._sel = (self._sel + 1) % n
            self.juego.audio.efecto('mover')
        elif ev.key in ACEPTAR:
            self.juego.audio.efecto('ok')
            destino = self._opciones[self._sel][1]
            if destino is None:
                self.juego.salir()
            else:
                self.juego.cambiar_escena(destino())
        elif ev.key == pygame.K_ESCAPE and not ES_WEB:
            self.juego.salir()

    def actualizar(self, dt):
        self._t += dt
        self._fondo.actualizar(dt)

    def dibujar(self, sup):
        self._fondo.dibujar(sup)
        t = self._t
        y = 24 + int(math.sin(t * 2) * 2)
        FUENTE.texto(sup, "CHOKI RUSH", C.ANCHO // 2, y, escala=4, color=C.AMARILLO,
                     sombra=(150, 50, 10), alinear='centro')

        alto = 12 + len(self._opciones) * 14
        ui.panel(sup, (90, 88, 140, alto))
        for i, (op, _d) in enumerate(self._opciones):
            yy = 96 + i * 14
            if i == self._sel:
                color = C.AMARILLO if int(t * 4) % 2 else C.NARANJA
                FUENTE.texto(sup, ">", 100, yy, color=color)
                FUENTE.texto(sup, op, 160, yy, color=color, alinear='centro')
            else:
                FUENTE.texto(sup, op, 160, yy, color=C.GRIS, alinear='centro')

        # el profe señalando el menú, abajo a la derecha
        profe = self.juego.recursos.profe_senalando(124)
        if profe is not None:
            sup.blit(profe, (C.ANCHO - profe.get_width() + 8,
                             C.ALTO - profe.get_height() + 10 + int(math.sin(t * 2.5) * 2)))

        # tu piloto saludando
        p = self.juego.piloto_personalizado
        if p is not None:
            m = self.juego.recursos.escalar(self.juego.recursos.muneco_de(p, int(t * 4) % 2), 2)
            sup.blit(m, (46 - m.get_width() // 2, 172 - m.get_height() - int(abs(math.sin(t * 5)) * 4)))
            FUENTE.texto(sup, p.nombre, 46, 176, color=C.VERDE, alinear='centro')

        online = "EN LÍNEA" if self.juego.servicio.disponible else "MODO LOCAL"
        FUENTE.texto(sup, f"MEJOR LOCAL: {self.juego.records.mejor:06d}", 8, 196, color=C.CIAN)
        FUENTE.texto(sup, "FLECHAS: MOVER  ENTER: ELEGIR", 8, 212, color=C.BLANCO)
        ayuda = "M: MÚSICA" if ES_WEB else "M: MÚSICA  F11: PANTALLA COMPLETA"
        FUENTE.texto(sup, ayuda, 8, 224, color=C.GRIS)
        FUENTE.texto(sup, online, 4, 4, color=C.VERDE if self.juego.servicio.disponible else C.GRIS)


# =====================================================================
#  Selección de piloto
# =====================================================================
class SeleccionPiloto(Escena):
    def __init__(self, juego):
        super().__init__(juego)
        self._fondo = FondoAnimado(juego)
        self._t = 0.0
        self._propio = juego.piloto_personalizado
        self._sel = len(PERSONAJES) if self._propio is not None else 0

    @property
    def _total(self):
        return len(PERSONAJES) + 1          # el último lugar es tu piloto (o "crear")

    def _actual(self):
        return PERSONAJES[self._sel] if self._sel < len(PERSONAJES) else self._propio

    def al_entrar(self):
        self.juego.audio.musica('menu')

    def manejar_evento(self, ev):
        if ev.type != pygame.KEYDOWN:
            return
        audio = self.juego.audio
        if ev.key in IZQUIERDA:
            self._sel = (self._sel - 1) % self._total
            audio.efecto('mover')
        elif ev.key in DERECHA:
            self._sel = (self._sel + 1) % self._total
            audio.efecto('mover')
        elif ev.key in ACEPTAR:
            audio.efecto('ok')
            p = self._actual()
            if p is None:
                self.juego.cambiar_escena(CreadorPiloto(self.juego))
            else:
                self.juego.cambiar_escena(SeleccionDificultad(self.juego, p))
        elif ev.key == pygame.K_e and self._sel == len(PERSONAJES):
            audio.efecto('ok')
            self.juego.cambiar_escena(CreadorPiloto(self.juego, self._propio))
        elif ev.key == pygame.K_ESCAPE:
            self.juego.cambiar_escena(MenuPrincipal(self.juego))

    def actualizar(self, dt):
        self._t += dt
        self._fondo.actualizar(dt)

    def dibujar(self, sup):
        self._fondo.dibujar(sup, 150)
        rec = self.juego.recursos
        p = self._actual()
        FUENTE.texto(sup, "ELIGE TU PILOTO", 160, 8, escala=2, color=C.AMARILLO, alinear='centro')

        if p is None:
            ui.panel(sup, (14, 30, 292, 150), borde=C.VERDE)
            FUENTE.texto(sup, "+", 70, 64, escala=8, color=C.VERDE, alinear='centro')
            FUENTE.texto(sup, "¡CREA TU PROPIO PILOTO!", 196, 50, color=C.VERDE, alinear='centro')
            for i, linea in enumerate(("SUBE TU FOTO Y EL JUEGO", "LA CONVIERTE EN PIXEL ART.",
                                       "", "ELIGE EL COLOR DE TU AUTO", f"Y REPARTE {PUNTOS_LIBRES} PUNTOS EN",
                                       "VELOCIDAD, ACELERACIÓN,", "MANEJO Y ECONOMÍA.")):
                FUENTE.texto(sup, linea, 196, 68 + i * 12, color=C.BLANCO, alinear='centro')
        else:
            ui.panel(sup, (14, 30, 292, 150), borde=p.color_auto)
            m = rec.escalar(rec.muneco_de(p, int(self._t * 4) % 2), 2)
            sup.blit(m, (52 - m.get_width() // 2, 102 - m.get_height() - int(abs(math.sin(self._t * 5)) * 3)))
            auto = rec.escalar(rec.auto_jugador(p), 3)
            sup.blit(auto, (100, 44 + int(math.sin(self._t * 5) * 2)))
            FUENTE.texto(sup, p.nombre, 140, 42, color=C.BLANCO)
            FUENTE.texto(sup, p.apodo, 140, 53, color=p.color_franja if not p.personalizado else C.VERDE)
            for i, (nombre, valor) in enumerate(p.estadisticas()):
                yy = 70 + i * 13
                FUENTE.texto(sup, nombre, 140, yy, color=C.GRIS)
                ui.barra(sup, (214, yy - 1, 82, 9), valor, p.color_auto, segmentos=5)
            for i, linea in enumerate(ui.envolver(p.descripcion, 44)):
                FUENTE.texto(sup, linea, 160, 132 + i * 11, color=C.BLANCO, alinear='centro')
            if p.personalizado:
                FUENTE.texto(sup, "E: EDITAR PILOTO", 160, 160, color=C.VERDE, alinear='centro')

        x0 = 160 - (self._total * 36) // 2
        for i in range(self._total):
            x = x0 + i * 36 + 4
            otro = PERSONAJES[i] if i < len(PERSONAJES) else self._propio
            if otro is None:
                pygame.draw.rect(sup, C.VERDE, (x, 188, 28, 28), 1)
                FUENTE.texto(sup, "+", x + 14, 192, escala=3, color=C.VERDE, alinear='centro')
            else:
                r = rec.retrato(otro)
                img = rec.escalar(r, 2) if r.get_width() <= 14 else pygame.transform.scale(r, (28, 28))
                sup.blit(img, (x, 188))
            if i == self._sel:
                pygame.draw.rect(sup, C.AMARILLO if int(self._t * 4) % 2 else C.BLANCO, (x - 3, 185, 34, 34), 1)
        FUENTE.texto(sup, "<", x0 - 12, 199, color=C.AMARILLO)
        FUENTE.texto(sup, ">", x0 + self._total * 36 + 6, 199, color=C.AMARILLO)
        FUENTE.texto(sup, "ENTER: ELEGIR   ESC: VOLVER", 160, 228, color=C.GRIS, alinear='centro')


# =====================================================================
#  Creador de piloto
# =====================================================================
class CreadorPiloto(Escena):
    CAMPOS = ("nombre", "foto", "color", 0, 1, 2, 3, "guardar")
    ETIQUETAS = ("VELOCIDAD", "ACELERACIÓN", "MANEJO", "ECONOMÍA")
    COLORES = ((226, 52, 52), (255, 150, 50), (240, 200, 40), (70, 190, 90), (40, 176, 200),
               (50, 90, 230), (156, 84, 226), (250, 110, 180), (235, 235, 235), (70, 70, 84))

    def __init__(self, juego, existente=None):
        super().__init__(juego)
        self._fondo = FondoAnimado(juego, 1)
        nombre = existente.nombre if existente else (juego.nombre_jugador or "")
        self._campo = CampoTexto(nombre, 10)
        self._niveles = list(existente.niveles) if existente else [NIVEL_MIN] * 4
        self._sprite = existente.sprite if existente else None
        self._retrato = existente.retrato if existente else None
        self._viendo_retrato = False
        color = existente.color_auto if existente else self.COLORES[0]
        self._color_i = self.COLORES.index(color) if color in self.COLORES else 0
        self._color_libre = None if color in self.COLORES else color
        self._foco = 0
        self._mensaje = "ESCRIBE TU NOMBRE"
        self._esperando_foto = False
        self._t = 0.0

    @property
    def captura_texto(self):
        return self._foco == 0

    @property
    def _puntos_libres(self):
        return PUNTOS_LIBRES - (sum(self._niveles) - 4 * NIVEL_MIN)

    def _color(self):
        return self._color_libre or self.COLORES[self._color_i]

    def _vista_previa(self):
        return PersonajePersonalizado.crear(self._campo.texto or "TU PILOTO", self._color(),
                                            self._niveles, self._sprite, self._retrato)

    def manejar_evento(self, ev):
        campo = self.CAMPOS[self._foco]
        if campo == "nombre" and self._campo.manejar(ev):
            return
        if ev.type != pygame.KEYDOWN:
            return
        if self._viendo_retrato:                    # cualquier tecla cierra la vista grande
            self._viendo_retrato = False
            return
        if ev.key == pygame.K_TAB and self._retrato is not None:
            self._viendo_retrato = True
            return
        audio = self.juego.audio
        solo_flechas = campo == "nombre"            # mientras escribes, W/A/S/D son letras
        arriba = ev.key == pygame.K_UP or (not solo_flechas and ev.key in ARRIBA)
        abajo = ev.key == pygame.K_DOWN or (not solo_flechas and ev.key in ABAJO)
        izq = ev.key == pygame.K_LEFT or (not solo_flechas and ev.key in IZQUIERDA)
        der = ev.key == pygame.K_RIGHT or (not solo_flechas and ev.key in DERECHA)

        if ev.key == pygame.K_ESCAPE:
            self.juego.cambiar_escena(SeleccionPiloto(self.juego))
        elif arriba or abajo:
            self._foco = (self._foco + (1 if abajo else -1)) % len(self.CAMPOS)
            audio.efecto('mover')
        elif (izq or der) and campo == "color":
            self._color_libre = None
            self._color_i = (self._color_i + (1 if der else -1)) % len(self.COLORES)
            audio.efecto('mover')
        elif (izq or der) and isinstance(campo, int):
            nuevo = self._niveles[campo] + (1 if der else -1)
            if NIVEL_MIN <= nuevo <= NIVEL_MAX and (not der or self._puntos_libres > 0):
                self._niveles[campo] = nuevo
                audio.efecto('mover')
            else:
                self._mensaje = "¡NO TE QUEDAN PUNTOS!" if der else "MÍNIMO 1"
        elif campo == "foto" and ev.key in (pygame.K_DELETE, pygame.K_BACKSPACE):
            self._sprite = None
            self._retrato = None
            self._mensaje = "FOTO QUITADA: USARÁS CASCO"
        elif ev.key in ACEPTAR:
            audio.efecto('ok')
            if campo == "nombre":
                self._foco = 1
            elif campo == "foto":
                self._esperando_foto = True
                self._mensaje = "ELIGE UNA IMAGEN..."
                self.juego.selector.abrir()
            elif campo == "guardar":
                self._guardar()
            else:
                self._foco = min(self._foco + 1, len(self.CAMPOS) - 1)

    def _guardar(self):
        if not self._campo.texto:
            self._foco = 0
            self._mensaje = "¡TU PILOTO NECESITA NOMBRE!"
            return
        if self._puntos_libres > 0:
            self._foco = 3
            self._mensaje = f"¡AÚN TE QUEDAN {self._puntos_libres} PUNTOS!"
            return
        p = self._vista_previa()
        self.juego.guardar_piloto(p)
        self.juego.cambiar_escena(SeleccionDificultad(self.juego, p))

    def actualizar(self, dt):
        self._t += dt
        self._fondo.actualizar(dt)
        armado = self.CAMPOS[self._foco] == "foto" and not self._esperando_foto
        if armado != getattr(self, "_armado", None):
            self._armado = armado
            self.juego.selector.armar(armado)
        if not self._esperando_foto:
            return
        res = self.juego.selector.resultado()
        if res is None:
            return
        self._esperando_foto = False
        estado, datos, info = res
        if estado == "ok":
            try:
                self._sprite, self._retrato = Pixelador().procesar_todo(datos, info or "foto.png")
                self._color_libre = None
                dominante = self._sprite.color_dominante()
                self._color_i = min(range(len(self.COLORES)), key=lambda i: sum(
                    (a - b) ** 2 for a, b in zip(self.COLORES[i], dominante)))
                self._mensaje = "¡LISTO! TAB: VER RETRATO EN GRANDE"
                self.juego.audio.efecto('moneda')
            except ValueError as e:
                self._mensaje = str(e).upper()[:34]
            except Exception:                 # nunca dejar que una foto rara congele el juego
                self._mensaje = "NO PUDE LEER ESA IMAGEN"
        elif estado == "cancelado":
            self._mensaje = "NO ELEGISTE NINGUNA IMAGEN"
        else:
            self._mensaje = "NO SE PUDO ABRIR LA IMAGEN"

    def dibujar(self, sup):
        self._fondo.dibujar(sup, 170)
        rec = self.juego.recursos
        t = self._t
        FUENTE.texto(sup, "CREA TU PILOTO", 160, 6, escala=2, color=C.AMARILLO, alinear='centro')
        p = self._vista_previa()

        ui.panel(sup, (6, 26, 104, 186), borde=p.color_auto)
        if self._retrato is not None:
            vista = rec.retrato_grande(self._retrato, 92)
            sup.blit(vista, (58 - vista.get_width() // 2, 31))
            m = rec.escalar(rec.muneco_de(p, int(t * 4) % 2), 2)
            sup.blit(m, (36 - m.get_width() // 2, 182 - m.get_height() - int(abs(math.sin(t * 5)) * 3)))
            auto = rec.escalar(rec.auto_jugador(p), 2)
            sup.blit(auto, (84 - auto.get_width() // 2, 182 - auto.get_height()))
            FUENTE.texto(sup, "TAB: VER GRANDE", 58, 194, color=C.VERDE, sombra=None, alinear='centro')
        else:
            m = rec.escalar(rec.muneco_de(p, int(t * 4) % 2), 3)
            sup.blit(m, (58 - m.get_width() // 2, 122 - m.get_height() - int(abs(math.sin(t * 5)) * 4)))
            auto = rec.escalar(rec.auto_jugador(p), 2)
            sup.blit(auto, (58 - auto.get_width() // 2, 140))
            FUENTE.texto(sup, "CON CASCO", 58, 194, color=C.GRIS, alinear='centro')
        FUENTE.texto(sup, p.nombre, 58, 184, color=C.BLANCO, alinear='centro')

        ui.panel(sup, (114, 26, 200, 186))
        x = 128

        def marca(i, y):
            activo = self._foco == i
            if activo:
                FUENTE.texto(sup, ">", 119, y, color=C.AMARILLO if int(t * 4) % 2 else C.NARANJA)
            return activo

        activo = marca(0, 36)
        FUENTE.texto(sup, "NOMBRE", x, 36, color=C.AMARILLO if activo else C.GRIS)
        self._campo.dibujar(sup, (x + 44, 32, 132, 14), activo, t)

        activo = marca(1, 56)
        FUENTE.texto(sup, "FOTO", x, 56, color=C.AMARILLO if activo else C.GRIS)
        boton = "[ENTER] SUBIR IMAGEN" if not self._esperando_foto else "ESPERANDO..."
        FUENTE.texto(sup, boton, x + 44, 56, color=C.BLANCO if activo else C.GRIS)
        if self._sprite is not None:
            FUENTE.texto(sup, "SUPR: QUITAR", x + 44, 66, color=(110, 110, 130), sombra=None)

        activo = marca(2, 80)
        FUENTE.texto(sup, "COLOR", x, 80, color=C.AMARILLO if activo else C.GRIS)
        FUENTE.texto(sup, "<", x + 44, 80, color=C.AMARILLO if activo else C.GRIS)
        pygame.draw.rect(sup, self._color(), (x + 54, 77, 40, 12))
        pygame.draw.rect(sup, C.BLANCO, (x + 54, 77, 40, 12), 1)
        FUENTE.texto(sup, ">", x + 98, 80, color=C.AMARILLO if activo else C.GRIS)

        for i, etiqueta in enumerate(self.ETIQUETAS):
            y = 102 + i * 15
            activo = marca(3 + i, y)
            FUENTE.texto(sup, etiqueta, x, y, color=C.AMARILLO if activo else C.GRIS)
            for k in range(NIVEL_MAX):
                lleno = k < self._niveles[i]
                pygame.draw.rect(sup, self._color() if lleno else (44, 40, 64), (x + 72 + k * 18, y - 1, 15, 9))
                pygame.draw.rect(sup, (8, 8, 14), (x + 72 + k * 18, y - 1, 15, 9), 1)
        libres = self._puntos_libres
        FUENTE.texto(sup, f"PUNTOS LIBRES: {libres}", x, 166, color=C.VERDE if libres else C.GRIS)

        activo = marca(7, 186)
        color = (C.AMARILLO if int(t * 4) % 2 else C.BLANCO) if activo else C.GRIS
        FUENTE.texto(sup, "[ GUARDAR Y CORRER ]", 214, 186, color=color, alinear='centro')

        FUENTE.texto(sup, self._mensaje, 160, 218, color=C.CIAN, alinear='centro')
        ayuda = {0: "ESCRIBE  -  FLECHAS: MOVERTE", 1: "ENTER: ELEGIR FOTO DE TU PC/CELULAR",
                 2: "IZQ/DER: CAMBIAR COLOR", 7: "ENTER: GUARDAR   ESC: CANCELAR"}.get(
            self._foco, "IZQ/DER: QUITAR O PONER PUNTOS")
        FUENTE.texto(sup, ayuda, 160, 230, color=C.GRIS, alinear='centro')
        if self._viendo_retrato and self._retrato is not None:
            dibujar_retrato_completo(sup, rec, self._retrato, p.nombre, self._t)


def dibujar_retrato_completo(sup, rec, retrato, nombre, t):
    """Muestra el retrato a tamaño real (211 px), pixel por pixel."""
    sup.fill((22, 18, 40))
    for x in range(0, C.ANCHO, 16):                 # cuadrícula de fondo estilo papel de patrón
        sup.fill((30, 26, 52), (x, 0, 1, C.ALTO))
    for y in range(0, C.ALTO, 16):
        sup.fill((30, 26, 52), (0, y, C.ANCHO, 1))
    img = rec.retrato_grande(retrato)
    x = 8
    y = (C.ALTO - img.get_height()) // 2
    sup.blit(img, (x, y))
    lx = x + img.get_width() + 8
    FUENTE.texto(sup, nombre, lx, 40, color=C.AMARILLO)
    FUENTE.texto(sup, f"{retrato.ancho - 2}X{retrato.alto - 2}", lx, 60, color=C.BLANCO)
    FUENTE.texto(sup, "PIXELES", lx, 70, color=C.GRIS)
    FUENTE.texto(sup, f"{len(retrato.paleta) - 1} COLORES", lx, 88, color=C.BLANCO)
    for i, color in enumerate(retrato.paleta[:-1]):
        sup.fill(color_desde_hex(color), (lx + (i % 4) * 18, 104 + (i // 4) * 14, 16, 12))
    if int(t * 2) % 2:
        FUENTE.texto(sup, "TECLA:", lx, 200, color=C.GRIS)
        FUENTE.texto(sup, "VOLVER", lx, 210, color=C.GRIS)


# =====================================================================
#  Dificultad
# =====================================================================
class SeleccionDificultad(Escena):
    def __init__(self, juego, personaje):
        super().__init__(juego)
        self._fondo = FondoAnimado(juego)
        self._personaje = personaje
        self._sel = 1
        self._t = 0.0

    def manejar_evento(self, ev):
        if ev.type != pygame.KEYDOWN:
            return
        if ev.key in IZQUIERDA or ev.key in ARRIBA:
            self._sel = (self._sel - 1) % len(DIFICULTADES)
            self.juego.audio.efecto('mover')
        elif ev.key in DERECHA or ev.key in ABAJO:
            self._sel = (self._sel + 1) % len(DIFICULTADES)
            self.juego.audio.efecto('mover')
        elif ev.key in ACEPTAR:
            self.juego.audio.efecto('ok')
            self.juego.cambiar_escena(Carrera(self.juego, self._personaje, DIFICULTADES[self._sel]))
        elif ev.key == pygame.K_ESCAPE:
            self.juego.cambiar_escena(SeleccionPiloto(self.juego))

    def actualizar(self, dt):
        self._t += dt
        self._fondo.actualizar(dt)

    def dibujar(self, sup):
        self._fondo.dibujar(sup, 160)
        FUENTE.texto(sup, "DIFICULTAD", 160, 14, escala=3, color=C.AMARILLO, alinear='centro')
        for i, d in enumerate(DIFICULTADES):
            x = 12 + i * 100
            activo = i == self._sel
            y = 50 - (int(abs(math.sin(self._t * 4)) * 4) if activo else 0)
            ui.panel(sup, (x, y, 96, 132), borde=d.color if activo else (70, 64, 100))
            FUENTE.texto(sup, d.nombre, x + 48, y + 10, escala=2, color=d.color if activo else C.GRIS,
                         alinear='centro')
            for k, linea in enumerate(ui.envolver(d.descripcion, 14)):
                FUENTE.texto(sup, linea, x + 48, y + 34 + k * 10, color=C.BLANCO if activo else C.GRIS,
                             alinear='centro')
            datos = (("TRÁFICO", f"{1 / d.factor_trafico:.1f}X"), ("GASTO", f"{d.factor_consumo:.1f}X"),
                     ("CHOQUE", f"-{int(d.costo_choque)}"), ("PUNTOS", f"X{d.factor_puntos:g}"))
            for k, (etq, val) in enumerate(datos):
                yy = y + 80 + k * 11
                FUENTE.texto(sup, etq, x + 8, yy, color=C.GRIS, sombra=None)
                FUENTE.texto(sup, val, x + 88, yy, color=d.color if activo else C.GRIS, alinear='der')
        m = self.juego.recursos.escalar(self.juego.recursos.muneco_de(self._personaje, int(self._t * 4) % 2), 1)
        sup.blit(m, (160 - m.get_width() // 2, 192))
        FUENTE.texto(sup, "ENTER: ¡A CORRER!   ESC: VOLVER", 160, 228, color=C.GRIS, alinear='centro')


# =====================================================================
#  Cómo jugar
# =====================================================================
class ComoJugar(Escena):
    """Tutorial estilo RPG: el profe explica el juego página por página."""

    def __init__(self, juego):
        super().__init__(juego)
        self._fondo = FondoAnimado(juego)
        self._t = 0.0
        self._paginas = (
            ("¡HOLA! SOY EL PROFE. BIENVENIDO A CHOKI RUSH. TE VOY A EXPLICAR CÓMO SE JUEGA.", self._v_inicio),
            ("MANTÉN ARRIBA (O Z) PARA ACELERAR Y ABAJO (O X) PARA FRENAR. CON IZQUIERDA Y DERECHA GIRAS.",
             self._v_controles),
            ("LA GASOLINA SE GASTA TODO EL TIEMPO. SI LLEGA A CERO, SE ACABA LA PARTIDA. ¡RECOGE BIDONES!",
             self._v_gasolina),
            ("ATRAPA LAS MONEDAS CON MI CARA: +500 PUNTOS. SI AGARRAS VARIAS SEGUIDAS HACES COMBO HASTA X4.",
             self._v_monedas),
            ("NO CHOQUES NI TE SALGAS DE LA PISTA. OJO: EL AUTO AZUL SE TE CIERRA Y EL ROSA VA EN ZIGZAG.",
             self._v_autos),
            ("EL ESCUDO TE HACE INVENCIBLE 6 SEGUNDOS. EL ACEITE Y EL HIELO TE HACEN DERRAPAR.", self._v_objetos),
            ("LLEGA A LA META DE LOS 4 NIVELES, CREA TU PILOTO CON TU FOTO Y ENTRA AL TOP 5. ¡SUERTE!",
             self._v_podio),
        )
        self._dialogo = DialogoProfe(juego.recursos, juego.audio, [t for t, _v in self._paginas])

    def _volver(self):
        self.juego.cambiar_escena(MenuPrincipal(self.juego))

    def manejar_evento(self, ev):
        if ev.type != pygame.KEYDOWN:
            return
        if ev.key == pygame.K_ESCAPE:
            self._volver()
        elif ev.key in ACEPTAR:
            self.juego.audio.efecto('ok')
            if not self._dialogo.avanzar():
                self._volver()

    def actualizar(self, dt):
        self._t += dt
        self._fondo.actualizar(dt)
        self._dialogo.actualizar(dt)

    def dibujar(self, sup):
        self._fondo.dibujar(sup, 160)
        FUENTE.texto(sup, "CÓMO JUGAR", 8, 6, color=C.AMARILLO)
        FUENTE.texto(sup, "ESC: SALIR", 312, 6, color=C.GRIS, alinear='der')
        panel = pygame.Rect(8, 20, 162, 140)
        ui.panel(sup, panel)
        pagina = min(self._dialogo.pagina, len(self._paginas) - 1)
        self._paginas[pagina][1](sup, panel)
        profe = self.juego.recursos.profe_senalando(150)
        if profe is not None:
            sup.blit(profe, (C.ANCHO - profe.get_width() + 6, 14 + int(math.sin(self._t * 2) * 2)))
        self._dialogo.dibujar(sup)

    # ---------- dibujos de cada página ----------
    def _v_inicio(self, sup, r):
        rec, t = self.juego.recursos, self._t
        FUENTE.texto(sup, "CHOKI RUSH", r.centerx, r.y + 14, escala=2, color=C.AMARILLO, alinear='centro')
        auto = rec.escalar(rec.auto_jugador(PERSONAJES[0]), 3)
        sup.blit(auto, (r.centerx - auto.get_width() // 2, r.y + 44 + int(math.sin(t * 6) * 3)))
        moneda = rec.cara_profe
        for k in range(3):
            sup.blit(moneda, (r.x + 14 + k * 50, r.bottom - 34 + int(math.sin(t * 4 + k) * 3)))

    def _v_controles(self, sup, r):
        t = self._t

        def tecla(x, y, simbolo, activa):
            color = C.AMARILLO if activa else (70, 64, 110)
            pygame.draw.rect(sup, (20, 18, 36), (x, y, 26, 24))
            pygame.draw.rect(sup, color, (x, y, 26, 24), 2)
            FUENTE.texto(sup, simbolo, x + 13, y + 8, color=color, alinear='centro')
        fase = int(t * 1.5) % 4
        cx, y0 = r.centerx, r.y + 20
        tecla(cx - 13, y0, "^", fase == 0)
        tecla(cx - 42, y0 + 28, "<", fase == 2)
        tecla(cx - 13, y0 + 28, "V", fase == 1)
        tecla(cx + 16, y0 + 28, ">", fase == 3)
        texto = ("ACELERAR", "FRENAR", "IZQUIERDA", "DERECHA")[fase]
        FUENTE.texto(sup, texto, cx, y0 + 66, color=C.VERDE, alinear='centro')
        FUENTE.texto(sup, "P: PAUSA   M: MÚSICA", cx, r.bottom - 16, color=C.GRIS, alinear='centro')

    def _v_gasolina(self, sup, r):
        rec, t = self.juego.recursos, self._t
        gas = rec.escalar(rec.gasolina(), 3)
        sup.blit(gas, (r.centerx - gas.get_width() // 2, r.y + 14 + int(math.sin(t * 4) * 3)))
        nivel = 1 - (t * 0.25) % 1
        color = C.VERDE if nivel > 0.5 else (C.AMARILLO if nivel > 0.2 else C.ROJO)
        FUENTE.texto(sup, "GASOLINA", r.x + 14, r.bottom - 40, color=C.GRIS)
        ui.barra(sup, (r.x + 14, r.bottom - 30, r.w - 28, 10), nivel, color, segmentos=5)

    def _v_monedas(self, sup, r):
        rec, t = self.juego.recursos, self._t
        grande = rec.escalar(rec.cara_profe, 3)
        sup.blit(grande, (r.centerx - grande.get_width() // 2, r.y + 10 + int(math.sin(t * 3) * 4)))
        combo = 1 + int(t * 1.5) % 4
        FUENTE.texto(sup, f"+{500 * combo}", r.centerx, r.bottom - 40, escala=2, color=C.AMARILLO,
                     alinear='centro')
        FUENTE.texto(sup, f"COMBO X{combo}", r.centerx, r.bottom - 18, color=C.NARANJA, alinear='centro')

    def _v_autos(self, sup, r):
        rec, t = self.juego.recursos, self._t
        autos = (rec.auto((40, 70, 220), (255, 214, 64)), rec.auto((250, 110, 180), (255, 255, 255)),
                 rec.camion((230, 130, 40), (175, 175, 182)))
        nombres = ("RIVAL", "ZIGZAG", "CAMIÓN")
        for k, (a, n) in enumerate(zip(autos, nombres)):
            a2 = rec.escalar(a, 2)
            x = r.x + 30 + k * 51 + (int(math.sin(t * 3) * 6) if k == 1 else 0)
            sup.blit(a2, (x - a2.get_width() // 2, r.y + 20))
            FUENTE.texto(sup, n, x, r.y + 90, color=C.BLANCO, alinear='centro')
        if int(t * 2) % 2:
            FUENTE.texto(sup, "¡NO CHOQUES!", r.centerx, r.bottom - 20, color=C.ROJO, alinear='centro')

    def _v_objetos(self, sup, r):
        rec, t = self.juego.recursos, self._t
        esc = rec.escalar(rec.escudo(), 3)
        sup.blit(esc, (r.x + 40 - esc.get_width() // 2, r.y + 24 + int(math.sin(t * 4) * 3)))
        FUENTE.texto(sup, "ESCUDO", r.x + 40, r.y + 72, color=C.CIAN, alinear='centro')
        man = rec.escalar(rec.mancha(NIVELES[1].tema), 3)
        sup.blit(man, (r.right - 44 - man.get_width() // 2, r.y + 34))
        FUENTE.texto(sup, "ACEITE", r.right - 44, r.y + 72, color=C.NARANJA, alinear='centro')
        if int(t * 2) % 2:
            FUENTE.texto(sup, "6 S INVENCIBLE", r.centerx, r.bottom - 22, color=C.VERDE, alinear='centro')

    def _v_podio(self, sup, r):
        rec, t = self.juego.recursos, self._t
        for k, p in enumerate(PERSONAJES[:3]):
            alto_bloque = (40, 28, 20)[k]
            x = r.centerx + (0, -48, 48)[k]
            sup.fill(Podio.COLORES[k], (x - 20, r.bottom - 10 - alto_bloque, 40, alto_bloque))
            FUENTE.texto(sup, str(k + 1), x, r.bottom - 6 - alto_bloque, color=C.BLANCO, alinear='centro')
            m = rec.escalar(rec.muneco_de(p, int(t * 4 + k) % 2), 2)
            salto = abs(math.sin(t * (4 if k == 0 else 6) + k)) * (8 if k == 0 else 3)
            sup.blit(m, (x - m.get_width() // 2, r.bottom - 10 - alto_bloque - m.get_height() - int(salto)))
        FUENTE.texto(sup, "TOP 5", r.centerx, r.y + 8, escala=2, color=C.AMARILLO, alinear='centro')


# =====================================================================
#  Clasificación (podio top 5)
# =====================================================================
class Clasificacion(Escena):
    FILTROS = (None, "facil", "normal", "dificil")
    NOMBRES_FILTRO = ("TODAS", "FÁCIL", "NORMAL", "DIFÍCIL")
    REFRESCO = 5.0

    def __init__(self, juego, resaltar=None, puesto=None):
        super().__init__(juego)
        self._fondo = FondoAnimado(juego, 3)
        self._resaltar = resaltar
        self._puesto = puesto
        self._filtro = 0
        self._peticion = None
        self._en_linea = False
        self._podio = None
        self._t_refresco = 0.0
        self._t = 0.0

    def al_entrar(self):
        self.juego.audio.musica('menu')
        self._pedir()

    def _pedir(self):
        self._t_refresco = self.REFRESCO
        if self.juego.servicio.disponible:
            self._peticion = self.juego.servicio.top(5, self.FILTROS[self._filtro])
        else:
            self._mostrar(self._locales(), False)

    def _locales(self):
        clave = self.FILTROS[self._filtro]
        return [r for r in self.juego.records.lista if clave is None or r.get("dificultad") == clave]

    def _mostrar(self, entradas, en_linea):
        anterior = self._podio.entradas if self._podio else None
        self._en_linea = en_linea
        if anterior != entradas:
            self._podio = Podio(self.juego.recursos, entradas, self._resaltar)

    def manejar_evento(self, ev):
        if ev.type != pygame.KEYDOWN:
            return
        if ev.key in IZQUIERDA or ev.key in DERECHA:
            paso = 1 if ev.key in DERECHA else -1
            self._filtro = (self._filtro + paso) % len(self.FILTROS)
            self._podio = None
            self.juego.audio.efecto('mover')
            self._pedir()
        elif ev.key in ACEPTAR or ev.key == pygame.K_ESCAPE:
            self.juego.audio.efecto('ok')
            self.juego.cambiar_escena(MenuPrincipal(self.juego))
        elif ev.key == pygame.K_r:
            self.juego.cambiar_escena(SeleccionPiloto(self.juego))

    def actualizar(self, dt):
        self._t += dt
        self._fondo.actualizar(dt)
        if self._podio:
            self._podio.actualizar(dt)
        pet = self._peticion
        if pet is not None and pet.terminada:
            self._peticion = None
            if pet.ok and isinstance(pet.datos, dict):
                self._mostrar(pet.datos.get("puntajes", []), True)
            else:
                self._mostrar(self._locales(), False)
        self._t_refresco -= dt
        if self._t_refresco <= 0 and self._peticion is None and self.juego.servicio.disponible:
            self._pedir()

    def dibujar(self, sup):
        self._fondo.dibujar(sup, 185)
        FUENTE.texto(sup, "TOP 5 PILOTOS", 160, 6, escala=2, color=C.AMARILLO, alinear='centro')
        filtro = self.NOMBRES_FILTRO[self._filtro]
        FUENTE.texto(sup, f"< {filtro} >", 160, 24, color=C.BLANCO, alinear='centro')
        if self._podio is None:
            FUENTE.texto(sup, "CARGANDO...", 160, 110, color=C.GRIS, alinear='centro')
        else:
            self._podio.dibujar(sup)
        fuente = "* EN VIVO *" if self._en_linea else "RÉCORDS LOCALES (SIN CONEXIÓN)"
        FUENTE.texto(sup, fuente, 160, 36, color=C.VERDE if self._en_linea else C.GRIS, alinear='centro')
        if self._puesto:
            FUENTE.texto(sup, f"TU PUESTO: #{self._puesto}", 316, 52, color=C.VERDE, alinear='der')
        FUENTE.texto(sup, "ENTER: MENÚ   R: JUGAR OTRA VEZ", 160, 230, color=C.GRIS, alinear='centro')


# =====================================================================
#  Fin de la partida
# =====================================================================
class FinPartida(Escena):
    def __init__(self, juego, gano, marcador, personaje, nivel, dificultad):
        super().__init__(juego)
        self._gano = gano
        self._marcador = marcador
        self._personaje = personaje
        self._nivel = nivel
        self._dificultad = dificultad
        self._fondo = FondoAnimado(juego, min(nivel, len(NIVELES)) - 1)
        defecto = personaje.nombre if personaje.personalizado else (juego.nombre_jugador or "")
        self._campo = CampoTexto(defecto, 10)
        self._fase = "nombre"           # nombre -> enviando
        self._peticion = None
        self._entrada = None
        self._t = 0.0
        self._musica_puesta = False

    @property
    def captura_texto(self):
        return self._fase == "nombre"

    def al_entrar(self):
        self.juego.audio.jingle('victoria' if self._gano else 'perder')

    def _entrada_puntaje(self, nombre):
        return {"nombre": nombre, "puntos": self._marcador.puntos, "nivel": self._nivel,
                "dificultad": self._dificultad.clave, "piloto": self._personaje.resumen_online()}

    def manejar_evento(self, ev):
        if self._fase != "nombre":
            return
        if self._campo.manejar(ev):
            return
        if ev.type == pygame.KEYDOWN and ev.key in (pygame.K_RETURN, pygame.K_KP_ENTER):
            nombre = self._campo.texto
            if not nombre:
                return
            self.juego.audio.efecto('ok')
            self.juego.nombre_jugador = nombre
            self._entrada = self._entrada_puntaje(nombre)
            self.juego.records.agregar(self._entrada)
            self._fase = "enviando"
            self._peticion = self.juego.servicio.enviar(self._entrada)
        elif ev.type == pygame.KEYDOWN and ev.key == pygame.K_ESCAPE:
            self.juego.cambiar_escena(MenuPrincipal(self.juego))

    def actualizar(self, dt):
        self._t += dt
        self._fondo.actualizar(dt)
        if self._t > 3.5 and not self._musica_puesta:
            self._musica_puesta = True
            self.juego.audio.musica('menu')
        if self._fase == "enviando" and self._peticion.terminada:
            puesto = None
            if self._peticion.ok and isinstance(self._peticion.datos, dict):
                puesto = self._peticion.datos.get("puesto")
            self.juego.cambiar_escena(Clasificacion(self.juego, self._entrada["nombre"], puesto))

    def dibujar(self, sup):
        self._fondo.dibujar(sup, 170)
        m = self._marcador
        if self._gano:
            FUENTE.texto(sup, "¡CAMPEÓN!", 160, 10, escala=3, color=C.AMARILLO,
                         sombra=(150, 50, 10), alinear='centro')
        else:
            FUENTE.texto(sup, "FIN DE LA CARRERA", 160, 14, escala=2, color=C.ROJO, alinear='centro')
        ui.panel(sup, (40, 38, 240, 88))
        datos = (("PUNTOS", f"{m.puntos:06d}", C.AMARILLO),
                 ("CARAS DEL PROFE", str(m.caras), C.AMARILLO),
                 ("AUTOS ADELANTADOS", str(m.adelantos), C.BLANCO),
                 ("NIVEL ALCANZADO", f"{self._nivel}/{len(NIVELES)}", C.CIAN),
                 ("DIFICULTAD", self._dificultad.nombre, self._dificultad.color))
        for i, (etq, val, color) in enumerate(datos):
            FUENTE.texto(sup, etq, 52, 47 + i * 15, color=C.GRIS)
            FUENTE.texto(sup, val, 268, 47 + i * 15, color=color, alinear='der')

        rec = self.juego.recursos
        retrato = getattr(self._personaje, "retrato", None)
        if retrato is not None:
            vista = rec.retrato_grande(retrato, 78)
            sup.blit(vista, (2, 130 + int(abs(math.sin(self._t * 3)) * 3)))
        else:
            mu = rec.escalar(rec.muneco_de(self._personaje, int(self._t * 4) % 2), 2)
            sup.blit(mu, (34 - mu.get_width() // 2, 190 - mu.get_height() - int(abs(math.sin(self._t * 5)) * 4)))

        if self._fase == "nombre":
            FUENTE.texto(sup, "ESCRIBE TU NOMBRE PARA LA CLASIFICACIÓN", 172, 136, color=C.VERDE, alinear='centro')
            self._campo.dibujar(sup, (112, 150, 120, 18), True, self._t)
            FUENTE.texto(sup, "ENTER: ENVIAR   ESC: NO GUARDAR", 172, 180, color=C.GRIS, alinear='centro')
        else:
            puntos = "." * (int(self._t * 3) % 4)
            FUENTE.texto(sup, f"ENVIANDO PUNTAJE{puntos}", 172, 156, color=C.CIAN, alinear='centro')
        frase = "¡EL PROFE ESTÁ ORGULLOSO!" if self._gano else "EL PROFE DICE: ¡OTRA VEZ!"
        FUENTE.texto(sup, frase, 172, 206, color=C.BLANCO, alinear='centro')
