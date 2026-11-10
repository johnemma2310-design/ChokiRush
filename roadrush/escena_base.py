"""Piezas compartidas por las escenas: clase base, fondo animado, campo de texto y podio."""
import math
import random
from abc import ABC, abstractmethod

import pygame

from . import config as C
from . import ui
from .dificultad import POR_CLAVE
from .fuente_pixel import FUENTE
from .pista import NIVELES, Pista
from .pixelador import SpritePixel, color_desde_hex

ARRIBA = (pygame.K_UP, pygame.K_w)
ABAJO = (pygame.K_DOWN, pygame.K_s)
IZQUIERDA = (pygame.K_LEFT, pygame.K_a)
DERECHA = (pygame.K_RIGHT, pygame.K_d)
ACEPTAR = (pygame.K_RETURN, pygame.K_KP_ENTER, pygame.K_SPACE)


class Escena(ABC):
    def __init__(self, juego):
        self.juego = juego

    @property
    def captura_texto(self):
        """True mientras el jugador escribe (desactiva atajos globales como M)."""
        return False

    def al_entrar(self):
        """Se llama cuando la escena pasa a ser la activa."""

    @abstractmethod
    def manejar_evento(self, evento):
        pass

    @abstractmethod
    def actualizar(self, dt):
        pass

    @abstractmethod
    def dibujar(self, sup):
        pass


class FondoAnimado:
    """Carretera desplazándose detrás de los menús."""

    def __init__(self, juego, indice_nivel=0):
        self._pista = Pista(NIVELES[indice_nivel], C.ANCHO, juego.recursos)
        self._camara = 600.0

    def actualizar(self, dt):
        self._camara += 140 * dt
        if self._camara > self._pista.nivel.longitud - 400:
            self._camara = 600.0

    def dibujar(self, sup, alfa=120):
        self._pista.dibujar(sup, self._camara)
        ui.velo(sup, alfa)


class CampoTexto:
    """Caja de texto de una línea (nombres). Acepta letras, números y espacios."""
    PERMITIDOS = set("ABCDEFGHIJKLMNÑOPQRSTUVWXYZ0123456789 ")

    def __init__(self, texto="", maximo=10):
        self._maximo = maximo
        self._ultima_keydown = ""
        self._texto = "".join(ch for ch in str(texto).upper() if ch in self.PERMITIDOS)[:maximo]

    @property
    def texto(self):
        return self._texto.strip()

    _hay_textinput = False   # en algunos navegadores no llega TEXTINPUT: se usa KEYDOWN.unicode

    def _agregar(self, texto):
        for ch in texto.upper():
            if ch in self.PERMITIDOS and len(self._texto) < self._maximo:
                self._texto += ch

    def manejar(self, ev):
        """Devuelve True si el evento fue de escritura."""
        if ev.type == pygame.TEXTINPUT:
            if not CampoTexto._hay_textinput:
                CampoTexto._hay_textinput = True
                # la primera letra ya pudo entrar por KEYDOWN: no duplicarla
                if self._ultima_keydown and self._texto.endswith(self._ultima_keydown) \
                        and ev.text.upper() == self._ultima_keydown:
                    self._texto = self._texto[:-1]
            self._agregar(ev.text)
            return True
        if ev.type != pygame.KEYDOWN:
            return False
        if ev.key == pygame.K_BACKSPACE:
            self._texto = self._texto[:-1]
            return True
        letra = getattr(ev, "unicode", "") or ""
        if letra and letra.upper() in self.PERMITIDOS:
            if not CampoTexto._hay_textinput:
                self._agregar(letra)
                self._ultima_keydown = letra.upper()
            return True
        return False

    def dibujar(self, sup, rect, activo, t):
        r = pygame.Rect(rect)
        pygame.draw.rect(sup, (10, 8, 22), r)
        pygame.draw.rect(sup, C.AMARILLO if activo else C.GRIS, r, 1)
        FUENTE.texto(sup, self._texto, r.x + 4, r.y + (r.h - 7) // 2, color=C.BLANCO)
        if activo and int(t * 3) % 2:
            x = r.x + 4 + FUENTE.ancho(self._texto) + 2
            sup.fill(C.AMARILLO, (x, r.y + 3, 5, r.h - 6))


class DialogoProfe:
    """Cuadro de diálogo estilo RPG: la cara del profe se balancea y el texto aparece letra por letra.

    paginas: lista de textos. Con `automatico=True` avanza solo (avisos durante la carrera)."""
    VELOCIDAD = 45          # letras por segundo

    def __init__(self, recursos, audio, paginas, rect=(4, 166, 312, 70), automatico=False, pausa=2.6):
        self._recursos = recursos
        self._audio = audio
        self._paginas = list(paginas)
        self._rect = pygame.Rect(rect)
        self._automatico = automatico
        self._pausa = pausa
        self._pagina = 0
        self._letras = 0.0
        self._espera = 0.0
        self._t = 0.0
        alto_cara = self._rect.h - 12
        self._cara = recursos.retrato_dialogo(alto_cara)
        ancho_texto = self._rect.w - self._cara.get_width() - 22
        self._max_chars = max(10, ancho_texto // FUENTE.AVANCE)
        self._lineas = [ui.envolver(p, self._max_chars) for p in self._paginas]

    @property
    def activo(self):
        return self._pagina < len(self._paginas)

    @property
    def pagina(self):
        return self._pagina

    def _total(self):
        return sum(len(l) for l in self._lineas[self._pagina])

    @property
    def pagina_completa(self):
        return self.activo and self._letras >= self._total()

    def avanzar(self):
        """ENTER: completa el texto o pasa a la siguiente página. Devuelve False al terminar."""
        if not self.activo:
            return False
        if not self.pagina_completa:
            self._letras = self._total()
            return True
        self._pagina += 1
        self._letras = 0.0
        self._espera = 0.0
        return self.activo

    def actualizar(self, dt):
        if not self.activo:
            return
        self._t += dt
        antes = int(self._letras)
        self._letras = min(self._total(), self._letras + self.VELOCIDAD * dt)
        if int(self._letras) // 4 != antes // 4 and int(self._letras) < self._total():
            self._audio.efecto('voz')                 # "bip" de voz estilo RPG
        if self._automatico and self.pagina_completa:
            self._espera += dt
            if self._espera >= self._pausa:
                self.avanzar()

    def dibujar(self, sup):
        if not self.activo:
            return
        r = self._rect
        ui.panel(sup, r, borde=C.AMARILLO, alfa=235)
        # cara balanceándose de lado a lado (y "hablando" mientras escribe)
        hablando = not self.pagina_completa
        dx = int(round(math.sin(self._t * 3.2) * 3))
        dy = -1 if hablando and int(self._t * 10) % 2 else 0
        marco = pygame.Rect(r.x + 6, r.y + 6, self._cara.get_width(), self._cara.get_height())
        anterior = sup.get_clip()
        sup.set_clip(marco)
        sup.fill((30, 90, 230), marco)
        sup.blit(self._cara, (marco.x + dx, marco.y + dy))
        sup.set_clip(anterior)
        pygame.draw.rect(sup, C.BLANCO, marco.inflate(2, 2), 1)
        # texto con efecto máquina de escribir
        x = marco.right + 8
        restantes = int(self._letras)
        for i, linea in enumerate(self._lineas[self._pagina]):
            if restantes <= 0:
                break
            FUENTE.texto(sup, linea[:restantes], x, r.y + 8 + i * 11, color=C.BLANCO)
            restantes -= len(linea)
        if self.pagina_completa and not self._automatico and int(self._t * 3) % 2:
            FUENTE.texto(sup, "ENTER >", r.right - 6, r.bottom - 11, color=C.AMARILLO, alinear='der')
        if len(self._paginas) > 1 and not self._automatico:
            FUENTE.texto(sup, f"{self._pagina + 1}/{len(self._paginas)}", x, r.bottom - 11, color=C.GRIS,
                         sombra=None)


def piloto_de_entrada(entrada):
    """Saca (sprite_cabeza, color) de una entrada de clasificación, con valores seguros."""
    from .personajes import PERSONAJES
    piloto = entrada.get("piloto") or {}
    try:
        return SpritePixel.desde_dict(piloto["sprite"]), color_desde_hex(piloto["color"])
    except (KeyError, TypeError, ValueError):
        return PERSONAJES[1].cabeza(), (150, 150, 162)


class Podio:
    """Top 5 al estilo de los concursos en vivo: bloques que suben y muñecos que bailan."""
    COLUMNAS = (3, 1, 0, 2, 4)                # qué puesto va en cada columna (izq -> der)
    ALTURAS = (62, 46, 36, 26, 18)
    COLORES = ((235, 185, 40), (190, 196, 214), (206, 128, 62), (96, 84, 150), (80, 72, 128))
    CONFETI = ((236, 64, 64), (255, 214, 64), (90, 220, 245), (90, 224, 110), (170, 100, 235))

    def __init__(self, recursos, entradas, resaltar=None, base=198):
        self._recursos = recursos
        self._entradas = list(entradas)[:5]
        self._pilotos = [piloto_de_entrada(e) for e in self._entradas]
        self._resaltar = (resaltar or "").upper()
        self._base = base
        self._t = 0.0
        self._rng = random.Random()
        self._confeti = []

    @property
    def entradas(self):
        return self._entradas

    def actualizar(self, dt):
        self._t += dt
        if self._entradas and self._t > 1.2 and len(self._confeti) < 70:
            for _ in range(2):
                self._confeti.append([self._rng.uniform(0, C.ANCHO), -4.0, self._rng.uniform(30, 70),
                                      self._rng.choice(self.CONFETI), self._rng.uniform(0, 6)])
        for c in self._confeti:
            c[1] += c[2] * dt
            c[4] += dt * 5
        self._confeti = [c for c in self._confeti if c[1] < C.ALTO]

    def dibujar(self, sup):
        for x, y, _v, color, fase in self._confeti:
            sup.fill(color, (int(x + math.sin(fase) * 3), int(y), 2, 2 if int(fase) % 2 else 1))
        if not self._entradas:
            FUENTE.texto(sup, "AÚN NO HAY PUNTAJES", C.ANCHO // 2, 110, color=C.GRIS, alinear='centro')
            FUENTE.texto(sup, "¡SÉ EL PRIMERO!", C.ANCHO // 2, 124, color=C.AMARILLO, alinear='centro')
            return
        for col, puesto in enumerate(self.COLUMNAS):
            if puesto < len(self._entradas):
                self._dibujar_columna(sup, col, puesto)

    def _dibujar_columna(self, sup, col, puesto):
        e = self._entradas[puesto]
        cx = 32 + col * 64
        retraso = (4 - puesto) * 0.25                     # el 1.º aparece de último, como en la tele
        avance = max(0.0, min(1.0, (self._t - retraso) / 0.6))
        avance = 1 - (1 - avance) ** 3
        alto = int(self.ALTURAS[puesto] * avance)
        tope = self._base - alto
        color = self.COLORES[puesto]
        if alto > 0:
            sup.fill(color, (cx - 28, tope, 56, alto))
            sup.fill(tuple(min(255, c + 50) for c in color), (cx - 28, tope, 56, 2))
            sup.fill(tuple(int(c * 0.7) for c in color), (cx - 28, tope + 2, 2, alto - 2))
            if alto > 16:
                FUENTE.texto(sup, str(puesto + 1), cx, tope + 4, escala=2, color=C.BLANCO,
                             sombra=(40, 30, 60), alinear='centro')
        if avance < 1:
            return

        visible = self._t - retraso - 0.6
        cuadro = int(self._t * 5 + col) % 2
        sprite, color_piloto = self._pilotos[puesto]
        muneco = self._recursos.escalar(self._recursos.muneco(sprite, color_piloto, cuadro), 2)
        if puesto == 0:
            salto = abs(math.sin(self._t * 4)) * 10
        else:
            salto = abs(math.sin(self._t * 6 + col)) * 3
        caida = max(0.0, 1 - visible / 0.35) * 60          # el muñeco cae desde arriba
        y = tope - muneco.get_height() - salto - caida
        sup.blit(muneco, (cx - muneco.get_width() // 2, int(y)))
        if puesto == 0:
            corona = self._recursos.escalar(self._recursos.corona(), 2)
            sup.blit(corona, (cx - corona.get_width() // 2, int(y) - corona.get_height() + 2))

        es_tuyo = self._resaltar and e.get("nombre", "").upper() == self._resaltar
        color_nombre = (C.VERDE if int(self._t * 5) % 2 else C.BLANCO) if es_tuyo else C.BLANCO
        FUENTE.texto(sup, str(e.get("nombre", "?"))[:9], cx, self._base + 4, color=color_nombre, alinear='centro')
        FUENTE.texto(sup, f"{int(e.get('puntos', 0)):06d}", cx, self._base + 14, color=C.AMARILLO, alinear='centro')
        dif = POR_CLAVE.get(e.get("dificultad"))
        if dif and alto > 30:
            FUENTE.texto(sup, dif.nombre[:3], cx, tope + 22, color=dif.color, sombra=None, alinear='centro')
        if es_tuyo:
            FUENTE.texto(sup, "TÚ", cx, int(y) - (26 if puesto == 0 else 12), color=C.VERDE, alinear='centro')
