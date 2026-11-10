"""Clase principal: inicializa pygame, administra la escena activa y el bucle de juego.

El bucle es `async` para que el mismo código corra en el navegador (pygbag necesita
devolver el control al navegador en cada cuadro con `await asyncio.sleep(0)`).
"""
import asyncio
import traceback

import pygame

from . import config as C
from . import plataforma
from . import ui
from .audio import GestorAudio
from .fuente_pixel import FUENTE
from .personajes import PersonajePersonalizado
from .pixelart import Recursos
from .records import GestorRecords, ServicioPuntajes


class Juego:
    def __init__(self):
        try:
            pygame.mixer.pre_init(22050, -16, 1, 512, allowedchanges=0)
        except TypeError:
            pygame.mixer.pre_init(22050, -16, 1, 512)
        pygame.init()
        if pygame.mixer.get_init() is None:
            try:
                pygame.mixer.init()
            except pygame.error:
                pass
        plataforma.preparar_navegador()
        pygame.display.set_caption(C.TITULO)
        banderas = 0 if plataforma.ES_WEB else pygame.SCALED
        self.pantalla = pygame.display.set_mode((C.ANCHO, C.ALTO), banderas)
        self.recursos = Recursos()
        pygame.display.set_icon(self.recursos.escalar(self.recursos.cara_profe, 2))
        self.audio = GestorAudio()
        self.almacen = plataforma.crear_almacen()
        self.selector = plataforma.crear_selector()
        self.servicio = ServicioPuntajes(plataforma.crear_cliente())
        self.records = GestorRecords(self.almacen)
        self._piloto = self._cargar_piloto()
        self.avisos_vistos = set()          # consejos del profe ya mostrados en esta sesión
        self._reloj = pygame.time.Clock()
        self._escena = None
        self._activo = True

    # ---------- datos del jugador ----------
    def _cargar_piloto(self):
        datos = self.almacen.leer("piloto")
        if not datos:
            return None
        try:
            return PersonajePersonalizado.desde_dict(datos)
        except (KeyError, TypeError, ValueError):
            return None

    @property
    def piloto_personalizado(self):
        return self._piloto

    def guardar_piloto(self, piloto):
        self._piloto = piloto
        self.almacen.escribir("piloto", piloto.a_dict())

    @property
    def nombre_jugador(self):
        return self.almacen.leer("jugador", "")

    @nombre_jugador.setter
    def nombre_jugador(self, nombre):
        self.almacen.escribir("jugador", str(nombre)[:10])

    # ---------- escenas ----------
    def cambiar_escena(self, escena):
        self.selector.armar(False)
        self._escena = escena
        escena.al_entrar()

    def salir(self):
        self._activo = False

    def _pantalla_carga(self, fraccion, mensaje):
        pygame.event.pump()
        s = self.pantalla
        s.fill(C.NEGRO)
        moneda = self.recursos.escalar(self.recursos.cara_profe, 3)
        s.blit(moneda, (C.ANCHO // 2 - moneda.get_width() // 2, 50))
        FUENTE.texto(s, "AFINANDO MOTORES...", C.ANCHO // 2, 130, color=C.AMARILLO, alinear='centro')
        ui.barra(s, (80, 146, 160, 8), fraccion, C.VERDE)
        FUENTE.texto(s, mensaje, C.ANCHO // 2, 162, color=C.GRIS, alinear='centro')
        pygame.display.flip()

    def _evento_global(self, ev):
        """Atajos que funcionan en cualquier pantalla. Devuelve True si consumió el evento."""
        if ev.type == pygame.QUIT:
            self.salir()
            return True
        if ev.type == pygame.KEYDOWN and ev.key == pygame.K_F11 and not plataforma.ES_WEB:
            pygame.display.toggle_fullscreen()
            return True
        if ev.type == pygame.KEYDOWN and ev.key == pygame.K_m and not self._escena.captura_texto:
            self.audio.alternar_silencio()
            return True
        return False

    async def ejecutar(self):
        from .escenas import MenuPrincipal   # import diferido: evita dependencias circulares
        self._pantalla_carga(0.0, "CARGANDO")
        await asyncio.sleep(0)
        self.audio.cargar(self._pantalla_carga)
        self.cambiar_escena(MenuPrincipal(self))
        while self._activo:
            dt = min(self._reloj.tick(C.FPS) / 1000.0, 1 / 20)
            try:
                self._cuadro(dt)
            except Exception:
                plataforma.reportar_error(traceback.format_exc())
                raise
            await asyncio.sleep(0)
        pygame.quit()

    def _cuadro(self, dt):
        self.servicio.actualizar()
        for ev in pygame.event.get():
            if not self._evento_global(ev):
                self._escena.manejar_evento(ev)
        self._escena.actualizar(dt)
        self._escena.dibujar(self.pantalla)
        if self.audio.silenciado:
            FUENTE.texto(self.pantalla, "SIN SONIDO", 4, C.ALTO - 10, color=C.GRIS)
        pygame.display.flip()
