"""Convierte cualquier foto en pixel art de verdad (no solo agrandar pixeles).

Pasos del algoritmo (la misma idea que usan herramientas como Pyxelate o Pixel-It,
pero escrito desde cero para que también corra en el navegador):
  1. Detección de la cara por color de piel (espacio YCbCr) y encuadre de la cabeza.
  2. Reducción a 22x22 promediando bloques de pixeles.
  3. Eliminación del fondo: máscara ovalada + relleno por inundación desde arriba y los
     lados (nunca se borran pixeles con color de piel).
  4. Ajuste de contraste y cuantización de color con k-means (paleta de 10 colores).
  5. Realce de saturación, recorte de bordes vacíos y contorno oscuro de 1 pixel.
"""
import colorsys
import io
import os
import random
import tempfile
from collections import deque
from dataclasses import dataclass

import pygame

DIGITOS = "0123456789abcdefghijklmnopqrstuv"   # hasta 32 colores por sprite
INDICE = {c: i for i, c in enumerate(DIGITOS)}


def _hex(color):
    return "#%02x%02x%02x" % tuple(color[:3])


def color_desde_hex(texto):
    texto = str(texto).lstrip("#")
    if len(texto) != 6:
        raise ValueError("color inválido")
    return tuple(int(texto[i:i + 2], 16) for i in (0, 2, 4))


@dataclass(frozen=True)
class SpritePixel:
    """Sprite compacto y serializable: paleta de hasta 16 colores + un caracter por pixel."""
    ancho: int
    alto: int
    paleta: tuple       # ('#rrggbb', ...)
    pixeles: str        # '0'-'f' = índice de paleta, '.' = transparente

    def a_dict(self):
        return {"w": self.ancho, "h": self.alto, "pal": list(self.paleta), "px": self.pixeles}

    @classmethod
    def desde_dict(cls, d):
        """Crea el sprite validando todo (los datos pueden venir de internet)."""
        try:
            w, h = int(d["w"]), int(d["h"])
            paleta = tuple(_hex(color_desde_hex(c)) for c in d["pal"])
            px = str(d["px"])
        except (KeyError, TypeError, ValueError) as e:
            raise ValueError(f"sprite inválido: {e}") from e
        if not (1 <= w <= 256 and 1 <= h <= 256) or not (1 <= len(paleta) <= 32) or len(px) != w * h:
            raise ValueError("sprite con tamaño inválido")
        validos = set(DIGITOS[:len(paleta)]) | {"."}
        if any(ch not in validos for ch in px):
            raise ValueError("sprite con pixeles inválidos")
        return cls(w, h, paleta, px)

    @classmethod
    def desde_plantilla(cls, plantilla, paleta_dict):
        ancho = max(len(f) for f in plantilla)
        colores, indices, px = [], {}, []
        for fila in plantilla:
            for ch in fila.ljust(ancho, "."):
                color = paleta_dict.get(ch)
                if color is None:
                    px.append(".")
                    continue
                clave = _hex(color)
                if clave not in indices:
                    indices[clave] = len(colores)
                    colores.append(clave)
                px.append(DIGITOS[indices[clave]])
        return cls(ancho, len(plantilla), tuple(colores), "".join(px))

    def a_superficie(self):
        sup = pygame.Surface((self.ancho, self.alto), pygame.SRCALPHA)
        colores = {DIGITOS[i]: color_desde_hex(c) for i, c in enumerate(self.paleta)}
        w = self.ancho
        for i, ch in enumerate(self.pixeles):
            if ch != ".":
                sup.set_at((i % w, i // w), colores[ch])
        return sup

    def color_dominante(self):
        cuenta = {}
        for ch in self.pixeles:
            if ch != ".":
                cuenta[ch] = cuenta.get(ch, 0) + 1
        if not cuenta:
            return (128, 128, 128)
        # ignora el contorno (el color más oscuro) al elegir el dominante
        candidatos = sorted(cuenta, key=lambda c: -cuenta[c])
        for ch in candidatos:
            color = color_desde_hex(self.paleta[INDICE[ch]])
            if sum(color) > 120:
                return color
        return color_desde_hex(self.paleta[INDICE[candidatos[0]]])


class Pixelador:
    CONTORNO = (24, 20, 36)
    ANALISIS = 96          # lado máximo de la copia pequeña usada para buscar la cara

    def __init__(self, tam=22, colores=10, semilla=1):
        self._tam = tam
        self._colores = colores
        self._semilla = semilla

    def procesar(self, datos, nombre="foto.png"):
        """Solo la cabeza pequeña (para el muñeco y las monedas)."""
        img = self._a_rgba(self._cargar(datos, nombre))
        return self._cabeza(img, self._detectar_cara(img))

    def procesar_todo(self, datos, nombre="foto.png", tam_retrato=211, colores_retrato=20):
        """Devuelve (cabeza pequeña, retrato grande estilo Makebead) a partir de la misma foto."""
        img = self._a_rgba(self._cargar(datos, nombre))
        cara = self._detectar_cara(img)
        return self._cabeza(img, cara), self._retrato(img, cara, tam_retrato, colores_retrato)

    def _cabeza(self, img, cara):
        t = self._tam
        if cara is None:
            w, h = img.get_size()
            lado = min(w, h)
            recorte = self._recorte_cuadrado(img, w / 2, (h - lado) / 4 + lado / 2, lado)
        else:
            x0, y0, x1, y1 = cara
            ancho, alto = x1 - x0, y1 - y0
            lado = max(ancho * 1.6, alto * 1.4)
            top = y0 - alto * 0.5                    # deja espacio para el pelo
            recorte = self._recorte_cuadrado(img, (x0 + x1) / 2, top + lado / 2, lado)
        pequena = pygame.transform.smoothscale(recorte, (t, t))
        pix = [[tuple(pequena.get_at((x, y))) for x in range(t)] for y in range(t)]
        opaco = [[pix[y][x][3] >= 128 for x in range(t)] for y in range(t)]
        piel = [[self._es_piel(pix[y][x]) for x in range(t)] for y in range(t)]
        cabeza = self._mascara_cabeza(pix, opaco, piel)
        if cabeza is not None:
            opaco = cabeza
        else:                                   # sin cara clara: método general
            self._mascara_ovalada(opaco)
            self._quitar_fondo(pix, opaco, piel)
        pix = self._contraste(pix, opaco)
        colores = [pix[y][x][:3] for y in range(t) for x in range(t) if opaco[y][x]]
        if len(colores) < 12:
            raise ValueError("No encontré una figura en la imagen")
        centros = [self._realzar(c) for c in self._kmeans(colores, self._colores)]
        return self._armar_sprite(pix, opaco, centros)

    # ---------- carga ----------
    @staticmethod
    def _cargar(datos, nombre):
        """Decodifica la imagen. En el navegador pygame no lee desde memoria,
        así que se escribe primero a un archivo temporal."""
        try:
            return pygame.image.load(io.BytesIO(datos), nombre)
        except Exception:
            pass
        extension = os.path.splitext(nombre)[1] or ".png"
        ruta = os.path.join(tempfile.gettempdir(), "roadrush_foto" + extension)
        try:
            with open(ruta, "wb") as f:
                f.write(datos)
            return pygame.image.load(ruta)
        except Exception as e:
            raise ValueError("No pude leer esa imagen") from e

    @staticmethod
    def _a_rgba(img):
        sup = pygame.Surface(img.get_size(), pygame.SRCALPHA)
        sup.blit(img, (0, 0))
        return sup

    # ---------- 1. encontrar la cabeza ----------
    @staticmethod
    def _es_piel(rgba):
        r, g, b = rgba[0], rgba[1], rgba[2]
        if len(rgba) > 3 and rgba[3] < 128:
            return False
        y = 0.299 * r + 0.587 * g + 0.114 * b
        cb = 128 - 0.168736 * r - 0.331264 * g + 0.5 * b
        cr = 128 + 0.5 * r - 0.418688 * g - 0.081312 * b
        return 77 <= cb <= 127 and 135 <= cr <= 175 and y > 45 and r > g and r > b

    def _detectar_cara(self, img):
        """Caja (x0, y0, x1, y1) de la cara en coordenadas de la foto, o None si no hay piel."""
        w, h = img.get_size()
        escala = min(1.0, self.ANALISIS / max(w, h))
        aw, ah = max(1, int(w * escala)), max(1, int(h * escala))
        chica = pygame.transform.smoothscale(img, (aw, ah))
        piel = [[self._es_piel(chica.get_at((x, y))) for x in range(aw)] for y in range(ah)]
        mejor = self._mayor_region(piel, aw, ah)
        if mejor is None or len(mejor) < 0.02 * aw * ah:
            return None
        xs = sorted(p[0] for p in mejor)
        ys = sorted(p[1] for p in mejor)
        # percentiles: ignora cuello, orejas o manos que estiran la caja
        x0, x1 = xs[int(len(xs) * 0.03)], xs[int(len(xs) * 0.97) - 1] + 1
        y0, y1 = ys[int(len(ys) * 0.02)], ys[int(len(ys) * 0.90) - 1] + 1
        return x0 / escala, y0 / escala, x1 / escala, y1 / escala

    @staticmethod
    def _recorte_cuadrado(img, cx, cy, lado):
        """Cuadrado centrado en (cx, cy); lo que cae fuera de la foto queda transparente."""
        lado = max(4, int(lado))
        cuadro = pygame.Surface((lado, lado), pygame.SRCALPHA)
        cuadro.blit(img, (-int(cx - lado / 2), -int(cy - lado / 2)))
        return cuadro

    # ---------- retrato grande (estilo Makebead: muchos colores, sin tramado) ----------
    def _retrato(self, img, cara, t, n_colores):
        w, h = img.get_size()
        if cara is None:
            lado = min(w, h)
            recorte = self._recorte_cuadrado(img, w / 2, lado / 2, lado)
        else:
            x0, y0, x1, y1 = cara
            ancho, alto = x1 - x0, y1 - y0
            lado = max(ancho * 2.5, alto * 2.0)      # cabeza y hombros
            top = y0 - alto * 0.55
            recorte = self._recorte_cuadrado(img, (x0 + x1) / 2, top + lado / 2, lado)
        pequena = pygame.transform.smoothscale(recorte, (t, t))
        pix = [[tuple(pequena.get_at((x, y))) for x in range(t)] for y in range(t)]
        opaco = [[p[3] >= 128 for p in fila] for fila in pix]
        piel = [[self._es_piel(p) for p in fila] for fila in pix]
        cara_local = None
        if cara is not None:
            k = t / recorte.get_width()
            izq = (x0 + x1) / 2 - recorte.get_width() / 2
            arriba = top
            cara_local = ((x0 - izq) * k, (y0 - arriba) * k, (x1 - izq) * k, (y1 - arriba) * k)
        self._quitar_fondo_retrato(pix, opaco, piel, cara_local)
        colores = [pix[y][x][:3] for y in range(t) for x in range(t) if opaco[y][x]]
        if len(colores) < 50:
            raise ValueError("No encontré una figura en la imagen")
        muestra = colores[::max(1, len(colores) // 2500)]   # k-means sobre una muestra: rápido en el navegador
        centros = self._kmeans(muestra, n_colores)
        return self._armar_sprite(pix, opaco, centros, recortar=False)

    def _quitar_fondo_retrato(self, pix, opaco, piel, cara=None, umbral=34, paso=13):
        """Inunda el fondo desde arriba y los lados; protege piel y pelo pegado a la cara."""
        t = len(pix)
        cabeza = self._mascara_cabeza(pix, opaco, piel, minimo=0.04) or [[False] * t for _ in range(t)]
        limite = int(t * 0.72)
        semillas = [(x, 0) for x in range(t)] + [(0, y) for y in range(limite)] + \
                   [(t - 1, y) for y in range(limite)]
        semillas += [(x, y) for y in range(t) for x in range(t)
                     if opaco[y][x] and any(not opaco[ny][nx] for nx, ny in self._vecinos(x, y, t)) and y < limite]
        fondo = [[False] * t for _ in range(t)]
        for sx, sy in semillas:
            if fondo[sy][sx] or not opaco[sy][sx] or piel[sy][sx] or cabeza[sy][sx]:
                continue
            semilla = pix[sy][sx][:3]
            cola = deque([(sx, sy)])
            fondo[sy][sx] = True
            while cola:
                x, y = cola.popleft()
                for nx, ny in self._vecinos(x, y, t):
                    if not fondo[ny][nx] and opaco[ny][nx] and not piel[ny][nx] and not cabeza[ny][nx] \
                            and self._dist2(pix[ny][nx][:3], semilla) < umbral * umbral \
                            and self._dist2(pix[ny][nx][:3], pix[y][x][:3]) < paso * paso:
                        fondo[ny][nx] = True
                        cola.append((nx, ny))
        figura = [[opaco[y][x] and not fondo[y][x] for x in range(t)] for y in range(t)]
        if cara is not None:
            # silueta de retrato: cabeza (piel + pelo) o busto (cuello y hombros); lo demás es fondo
            # aunque tenga el mismo color que la ropa (paredes, monitores, cables...)
            fx0, fy0, fx1, fy1 = cara
            cx, ancho = (fx0 + fx1) / 2, fx1 - fx0
            barbilla = fy1
            for y in range(t):
                for x in range(t):
                    if not figura[y][x] or cabeza[y][x] or piel[y][x]:
                        continue
                    alto = fy1 - fy0
                    if y < barbilla - 0.1 * alto:                     # óvalo de la cabeza: pelo y orejas
                        dentro = ((x - cx) / (0.62 * ancho)) ** 2 + \
                                 ((y - (fy0 + 0.4 * alto)) / (0.85 * alto)) ** 2 < 1.0
                    else:
                        bajada = y - barbilla
                        mitad = 0.36 * ancho + max(0.0, bajada - 0.08 * ancho) * 2.4
                        dentro = abs(x - cx) < min(mitad, 1.9 * ancho)
                    if not dentro:
                        figura[y][x] = False
        # quedarse con la figura principal (conectada a la cara) y rellenar huecos
        principal = self._mayor_region(figura, t, t)
        if principal is None or len(principal) < 0.2 * t * t:
            return                                # no se pudo separar: se deja el fondo
        final = [[False] * t for _ in range(t)]
        for x, y in principal:
            final[y][x] = True
        afuera = [[False] * t for _ in range(t)]
        cola = deque((x, y) for y in range(t) for x in range(t)
                     if (x in (0, t - 1) or y in (0, t - 1)) and not final[y][x])
        for x, y in cola:
            afuera[y][x] = True
        while cola:
            x, y = cola.popleft()
            for nx, ny in self._vecinos(x, y, t):
                if not afuera[ny][nx] and not final[ny][nx]:
                    afuera[ny][nx] = True
                    cola.append((nx, ny))
        for y in range(t):
            for x in range(t):
                opaco[y][x] = opaco[y][x] and not afuera[y][x]

    @staticmethod
    def _mayor_region(mapa, w, h):
        visto = [[False] * w for _ in range(h)]
        mejor = None
        for y in range(h):
            for x in range(w):
                if not mapa[y][x] or visto[y][x]:
                    continue
                region, cola = [], deque([(x, y)])
                visto[y][x] = True
                while cola:
                    px, py = cola.popleft()
                    region.append((px, py))
                    for nx, ny in ((px + 1, py), (px - 1, py), (px, py + 1), (px, py - 1)):
                        if 0 <= nx < w and 0 <= ny < h and mapa[ny][nx] and not visto[ny][nx]:
                            visto[ny][nx] = True
                            cola.append((nx, ny))
                if mejor is None or len(region) > len(mejor):
                    mejor = region
        return mejor

    # ---------- 2. fondo ----------
    def _mascara_cabeza(self, pix, opaco, piel, minimo=0.15):
        """Cabeza = piel + pelo (pixeles oscuros pegados a la piel) + huecos rellenos (ojos, boca).
        Devuelve None si la foto no parece un retrato."""
        t = len(pix)
        region_piel = self._mayor_region(piel, t, t)
        if region_piel is None or len(region_piel) < minimo * t * t:
            return None

        def lum(p):
            return 0.299 * p[0] + 0.587 * p[1] + 0.114 * p[2]
        sx0 = min(p[0] for p in region_piel)
        sx1 = max(p[0] for p in region_piel)
        sy0 = min(p[1] for p in region_piel)
        sy1 = max(p[1] for p in region_piel)
        mitad = sy0 + (sy1 - sy0) * 0.45

        def puede_ser_pelo(x, y):
            # pelo/patillas arriba de los ojos, o barba dentro del ancho de la cara (no monitores ni sillas)
            return y <= mitad or sx0 <= x <= sx1
        oscuro = [[opaco[y][x] and not piel[y][x] and lum(pix[y][x]) < 95 and puede_ser_pelo(x, y)
                   for x in range(t)] for y in range(t)]
        cabeza = [[False] * t for _ in range(t)]
        cola = deque(region_piel)
        for x, y in region_piel:
            cabeza[y][x] = True
        while cola:                              # crece desde la piel hacia el pelo oscuro
            x, y = cola.popleft()
            for nx, ny in self._vecinos(x, y, t):
                if not cabeza[ny][nx] and (oscuro[ny][nx] or piel[ny][nx]):
                    cabeza[ny][nx] = True
                    cola.append((nx, ny))
        # rellena huecos: lo que no se puede alcanzar desde el borde sin cruzar la cabeza
        afuera = [[False] * t for _ in range(t)]
        cola = deque((x, y) for y in range(t) for x in range(t)
                     if (x in (0, t - 1) or y in (0, t - 1)) and not cabeza[y][x])
        for x, y in cola:
            afuera[y][x] = True
        while cola:
            x, y = cola.popleft()
            for nx, ny in self._vecinos(x, y, t):
                if not afuera[ny][nx] and not cabeza[ny][nx]:
                    afuera[ny][nx] = True
                    cola.append((nx, ny))
        resultado = [[opaco[y][x] and not afuera[y][x] for x in range(t)] for y in range(t)]
        # suaviza: quita puntas sueltas
        for y in range(t):
            for x in range(t):
                if resultado[y][x] and sum(1 for nx, ny in self._vecinos(x, y, t) if resultado[ny][nx]) <= 1:
                    resultado[y][x] = False
        total = sum(f.count(True) for f in resultado)
        if total > 0.88 * t * t:                 # fondo oscuro: el "pelo" se tragó todo
            return None
        return resultado

    @staticmethod
    def _mascara_ovalada(opaco):
        t = len(opaco)
        c = (t - 1) / 2
        rx, ry = t * 0.50, t * 0.54
        for y in range(t):
            for x in range(t):
                if ((x - c) / rx) ** 2 + ((y - c - t * 0.03) / ry) ** 2 > 1.0:
                    opaco[y][x] = False

    @staticmethod
    def _dist2(a, b):
        return (a[0] - b[0]) ** 2 + (a[1] - b[1]) ** 2 + (a[2] - b[2]) ** 2

    def _vecinos(self, x, y, t):
        for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            if 0 <= x + dx < t and 0 <= y + dy < t:
                yield x + dx, y + dy

    def _quitar_fondo(self, pix, opaco, piel, umbral=40, paso=26):
        t = len(pix)
        limite = t * 3 // 4            # abajo suele estar el cuello o la ropa: no se siembra ahí
        semillas = []
        for y in range(limite):
            for x in range(t):
                borde = x in (0, t - 1) or y == 0 or any(not opaco[ny][nx] for nx, ny in self._vecinos(x, y, t))
                if opaco[y][x] and borde:
                    semillas.append((x, y))
        quitar = set()
        visto = [[False] * t for _ in range(t)]
        for sx, sy in semillas:
            if visto[sy][sx] or piel[sy][sx]:
                continue
            semilla = pix[sy][sx][:3]
            cola = deque([(sx, sy)])
            visto[sy][sx] = True
            while cola:
                x, y = cola.popleft()
                quitar.add((x, y))
                for nx, ny in self._vecinos(x, y, t):
                    if not visto[ny][nx] and opaco[ny][nx] and not piel[ny][nx] \
                            and self._dist2(pix[ny][nx][:3], semilla) < umbral * umbral \
                            and self._dist2(pix[ny][nx][:3], pix[y][x][:3]) < paso * paso:
                        visto[ny][nx] = True
                        cola.append((nx, ny))
        quedan = sum(fila.count(True) for fila in opaco) - len(quitar)
        if quedan >= 0.25 * t * t:
            for x, y in quitar:
                opaco[y][x] = False
            # restos del fondo pegados al borde (mezcla pelo/pared): muy claros o muy parecidos al fondo quitado
            fondo = [pix[y][x][:3] for x, y in quitar]
            for _ in range(2):
                for y in range(limite):
                    for x in range(t):
                        if not opaco[y][x] or piel[y][x]:
                            continue
                        if not any(not opaco[ny][nx] for nx, ny in self._vecinos(x, y, t)) and x not in (0, t - 1):
                            continue
                        p = pix[y][x][:3]
                        if sum(p) > 600 or any(self._dist2(p, f) < 30 * 30 for f in fondo[::3]):
                            opaco[y][x] = False
        # limpia pixeles sueltos (con 0 o 1 vecino opaco)
        for y in range(t):
            for x in range(t):
                if opaco[y][x] and sum(1 for nx, ny in self._vecinos(x, y, t) if opaco[ny][nx]) <= 1:
                    opaco[y][x] = False

    # ---------- 3. color ----------
    @staticmethod
    def _contraste(pix, opaco):
        """Estira la luminosidad entre los percentiles 3 y 97 para que ojos y boca resalten."""
        lums = sorted(0.299 * p[0] + 0.587 * p[1] + 0.114 * p[2]
                      for fila, fo in zip(pix, opaco) for p, o in zip(fila, fo) if o)
        if len(lums) < 10:
            return pix
        bajo, alto = lums[int(len(lums) * 0.02)], lums[int(len(lums) * 0.99) - 1]
        if alto - bajo < 20:
            return pix
        k = min(1.6, 220 / (alto - bajo))

        def ajustar(v):
            return max(0, min(255, int((v - bajo) * k + 18)))
        return [[(ajustar(p[0]), ajustar(p[1]), ajustar(p[2]), p[3]) for p in fila] for fila in pix]

    def _kmeans(self, colores, k):
        unicos = list(set(colores))
        if len(unicos) <= k:
            return unicos
        rng = random.Random(self._semilla)
        centros = [rng.choice(colores)]
        while len(centros) < k:                       # inicialización k-means++
            d2 = [min(self._dist2(c, m) for m in centros) for c in colores]
            total = sum(d2)
            if total == 0:
                break
            r = rng.random() * total
            acumulado = 0
            for c, d in zip(colores, d2):
                acumulado += d
                if acumulado >= r:
                    centros.append(c)
                    break
        for _ in range(15):
            grupos = [[] for _ in centros]
            for c in colores:
                grupos[self._mas_cercano(c, centros)].append(c)
            nuevos = [tuple(sum(v[i] for v in g) / len(g) for i in range(3)) if g else centros[j]
                      for j, g in enumerate(grupos)]
            if nuevos == centros:
                break
            centros = nuevos
        return [tuple(int(round(v)) for v in c) for c in centros]

    def _mas_cercano(self, color, centros):
        return min(range(len(centros)), key=lambda i: self._dist2(color, centros[i]))

    @staticmethod
    def _realzar(color):
        h, s, v = colorsys.rgb_to_hsv(*(c / 255 for c in color))
        r, g, b = colorsys.hsv_to_rgb(h, min(1.0, s * 1.2), v)
        return int(r * 255), int(g * 255), int(b * 255)

    # ---------- 4. sprite final ----------
    def _armar_sprite(self, pix, opaco, centros, recortar=True):
        t = len(pix)
        filas = [y for y in range(t) if any(opaco[y])]
        cols = [x for x in range(t) if any(opaco[y][x] for y in range(t))]
        y0, y1, x0, x1 = filas[0], filas[-1], cols[0], cols[-1]
        if not recortar:
            y0, y1, x0, x1 = 0, t - 1, 0, t - 1
        cache = {}
        w, h = x1 - x0 + 3, y1 - y0 + 3
        paleta = [_hex(c) for c in centros] + [_hex(self.CONTORNO)]
        idx_contorno = DIGITOS[len(centros)]
        salida = [["."] * w for _ in range(h)]
        for y in range(y0, y1 + 1):
            for x in range(x0, x1 + 1):
                if opaco[y][x]:
                    color = pix[y][x][:3]
                    i = cache.get(color)
                    if i is None:
                        i = cache[color] = self._mas_cercano(color, centros)
                    salida[y - y0 + 1][x - x0 + 1] = DIGITOS[i]
        for y in range(h):
            for x in range(w):
                if salida[y][x] == "." and any(salida[ny][nx] not in (".", idx_contorno)
                                               for nx, ny in self._vecinos2(x, y, w, h)):
                    salida[y][x] = idx_contorno
        return SpritePixel(w, h, tuple(paleta), "".join("".join(f) for f in salida))

    @staticmethod
    def _vecinos2(x, y, w, h):
        for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            if 0 <= x + dx < w and 0 <= y + dy < h:
                yield x + dx, y + dy


