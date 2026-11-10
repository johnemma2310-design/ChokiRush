"""Música chiptune ORIGINAL y efectos de sonido, sintetizados por código al iniciar.

No se usa ningún archivo de audio externo: todo se genera con ondas cuadradas,
triangulares, senoidales y ruido (como las consolas de 8 bits), así que no hay
problemas de derechos de autor.
"""
import array
import math
import random

import pygame


def _hz(nota_midi):
    return 440.0 * 2 ** ((nota_midi - 69) / 12)


class Sintetizador:
    def __init__(self, frecuencia_muestreo):
        self.fs = frecuencia_muestreo
        self._rng = random.Random(7)

    def lienzo(self, segundos):
        return [0.0] * int(segundos * self.fs)

    def tono(self, buf, t0, dur, hz, forma='cuadrada', vol=0.2, hz_fin=None,
             ataque=0.004, liberacion=0.03, sostenido=0.7):
        fs = self.fs
        i0 = int(t0 * fs)
        n = max(1, int(dur * fs))
        fin = min(len(buf), i0 + n)
        if fin <= i0:
            return
        a = max(1, int(ataque * fs))
        r = max(1, int(liberacion * fs))
        paso = hz / fs
        dpaso = ((hz_fin if hz_fin is not None else hz) - hz) / fs / n
        caida = 1.0 - sostenido
        fase = 0.0
        sin = math.sin
        for k in range(fin - i0):
            env = k / a if k < a else 1.0 - caida * (k / n)
            if n - k < r:
                env *= (n - k) / r
            f = fase - int(fase)
            if forma == 'cuadrada':
                s = 1.0 if f < 0.5 else -1.0
            elif forma == 'pulso':
                s = 1.0 if f < 0.25 else -1.0
            elif forma == 'triangulo':
                s = 4 * f - 1 if f < 0.5 else 3 - 4 * f
            else:
                s = sin(6.283185307 * f)
            buf[i0 + k] += s * env * vol
            fase += paso
            paso += dpaso

    def ruido(self, buf, t0, dur, vol, paso=1):
        fs = self.fs
        i0 = int(t0 * fs)
        n = max(1, int(dur * fs))
        fin = min(len(buf), i0 + n)
        aleatorio = self._rng.random
        v = 0.0
        for k in range(fin - i0):
            if k % paso == 0:
                v = aleatorio() * 2 - 1
            e = 1 - k / n
            buf[i0 + k] += v * vol * e * e

    @staticmethod
    def a_muestras(buf, ganancia=1.0):
        """Lista de floats -> array de enteros de 16 bits (mono)."""
        return array.array('h', [
            int(32000 * (1.0 if s > 1.0 else (-1.0 if s < -1.0 else s)))
            for s in (x * ganancia for x in buf)
        ])

    @classmethod
    def a_sonido(cls, buf, canales, ganancia=1.0):
        datos = cls.a_muestras(buf, ganancia)
        if canales > 1:
            multi = array.array('h', bytes(2 * len(datos) * canales))
            for c in range(canales):
                multi[c::canales] = datos
            datos = multi
        return pygame.mixer.Sound(buffer=datos.tobytes())


# ---------------------------------------------------------------------
#  Composición original (La menor: Am - F - C - G - Am - F - G - E)
# ---------------------------------------------------------------------
ACORDES = ((57, 60, 64), (53, 57, 60), (55, 60, 64), (55, 59, 62),
           (57, 60, 64), (53, 57, 60), (55, 59, 62), (56, 59, 64))
BAJOS = (45, 41, 48, 43, 45, 41, 43, 40)

MELODIA_A = (
    "69 - 72 76 - 74 72 71",
    "72 - 69 65 - 69 72 -",
    "67 - 72 76 - 79 76 74",
    "74 - 71 67 - 71 74 -",
    "76 - 74 72 - 74 76 81",
    "79 - 77 76 - 74 72 -",
    "71 72 74 79 - 77 76 74",
    "76 - - 75 - 71 68 64",
)
MELODIA_B = (
    "81 - 79 76 - 72 76 -",
    "77 - 76 72 - 69 72 -",
    "76 - 79 84 - 83 79 76",
    "74 - - 79 - 74 71 -",
    "72 74 76 - 72 74 76 79",
    "77 - 76 - 74 - 72 -",
    "74 76 77 79 - 81 - 83",
    "80 - - - 76 - 71 -",
)


def _eventos(barras):
    """'69 - 72' -> [[inicio, duracion, nota], ...] en corcheas. '-' alarga, '.' es silencio."""
    eventos, pos = [], 0
    for barra in barras:
        for tok in barra.split():
            if tok == '-':
                if eventos:
                    eventos[-1][1] += 1
            elif tok != '.':
                eventos.append([pos, 1, int(tok)])
            pos += 1
    return eventos


def _componer(s, bpm, melodia, forma_melodia, vol_melodia, bateria, eco):
    c = 60 / bpm / 2                     # duración de una corchea
    base = s.lienzo(len(ACORDES) * 8 * c)
    patron = (0, 1, 2, 1)
    for b, (acorde, raiz) in enumerate(zip(ACORDES, BAJOS)):
        t0 = b * 8 * c
        for i in range(8):
            s.tono(base, t0 + i * c, c * 0.9, _hz(raiz + (12 if i % 2 else 0)), 'triangulo', 0.2)
        for i in range(16):
            s.tono(base, t0 + i * c / 2, c * 0.4, _hz(acorde[patron[i % 4]] + 12), 'pulso', 0.04,
                   liberacion=0.01)
        if bateria:
            for i in range(8):
                s.ruido(base, t0 + i * c, 0.03, 0.05)
            for i in (0, 4) + ((7,) if b % 2 else ()):
                s.tono(base, t0 + i * c, 0.13, 150, 'seno', 0.45, hz_fin=40, sostenido=0.3)
            for i in (2, 6):
                s.ruido(base, t0 + i * c, 0.14, 0.2, paso=2)
                s.tono(base, t0 + i * c, 0.07, 190, 'triangulo', 0.1, hz_fin=120)
    pista = base * max(1, len(melodia) // len(ACORDES))
    for inicio, dur, nota in _eventos(melodia):
        t, d = inicio * c, dur * c * 0.92
        s.tono(pista, t, d, _hz(nota), forma_melodia, vol_melodia, sostenido=0.6)
        if eco:
            s.tono(pista, t + 3 * c, d, _hz(nota), forma_melodia, vol_melodia * 0.3, sostenido=0.6)
    return pista


def componer_menu(s):
    return _componer(s, 108, MELODIA_A, 'triangulo', 0.2, bateria=False, eco=False)


def componer_carrera(s):
    return _componer(s, 152, MELODIA_A + MELODIA_B, 'pulso', 0.11, bateria=True, eco=True)


def _secuencia(s, buf, notas, c, forma, vol):
    for nota, inicio, dur in notas:
        s.tono(buf, inicio * c, dur * c * 0.95, _hz(nota), forma, vol)


def crear_jingles(s):
    j = {}
    b = s.lienzo(1.9)
    _secuencia(s, b, ((72, 0, 1), (76, 1, 1), (79, 2, 1), (84, 3, 3), (83, 6, 1), (84, 7, 3)), 0.17, 'pulso', 0.16)
    _secuencia(s, b, ((64, 0, 1), (67, 1, 1), (72, 2, 1), (76, 3, 3), (74, 6, 1), (76, 7, 3)), 0.17, 'cuadrada', 0.07)
    s.tono(b, 0, 1.8, _hz(48), 'triangulo', 0.25)
    j['victoria'] = b
    b = s.lienzo(1.9)
    _secuencia(s, b, ((72, 0, 2), (71, 2, 2), (70, 4, 2), (69, 6, 5)), 0.16, 'cuadrada', 0.15)
    s.tono(b, 0.96, 0.9, _hz(45), 'triangulo', 0.28)
    j['perder'] = b
    b = s.lienzo(1.0)
    _secuencia(s, b, ((76, 0, 1), (79, 1, 1), (84, 2, 1), (88, 3, 4)), 0.1, 'pulso', 0.16)
    s.tono(b, 0.3, 0.6, _hz(60), 'triangulo', 0.25)
    j['nivel'] = b
    return j


def crear_efectos(s):
    e = {}
    b = s.lienzo(0.2); s.tono(b, 0, 0.06, _hz(83), 'cuadrada', 0.2); s.tono(b, 0.06, 0.14, _hz(88), 'cuadrada', 0.2); e['moneda'] = b
    b = s.lienzo(0.32)
    for i, n in enumerate((60, 64, 67, 72)):
        s.tono(b, i * 0.06, 0.1, _hz(n), 'triangulo', 0.35)
    e['gasolina'] = b
    b = s.lienzo(0.4); s.tono(b, 0, 0.4, 300, 'pulso', 0.14, hz_fin=1400); e['escudo'] = b
    b = s.lienzo(0.7); s.ruido(b, 0, 0.7, 0.45, paso=3); s.tono(b, 0, 0.45, 140, 'seno', 0.5, hz_fin=30); e['choque'] = b
    b = s.lienzo(0.5); s.ruido(b, 0, 0.5, 0.12); s.tono(b, 0, 0.5, 900, 'cuadrada', 0.05, hz_fin=500); e['derrape'] = b
    b = s.lienzo(0.18); s.tono(b, 0, 0.16, _hz(69), 'cuadrada', 0.2); e['cuenta'] = b
    b = s.lienzo(0.45); s.tono(b, 0, 0.42, _hz(81), 'cuadrada', 0.2); e['ya'] = b
    b = s.lienzo(0.05); s.tono(b, 0, 0.04, 1100, 'pulso', 0.1); e['mover'] = b
    b = s.lienzo(0.05); s.tono(b, 0, 0.035, 520, 'cuadrada', 0.07, hz_fin=640); e['voz'] = b
    b = s.lienzo(0.16); s.tono(b, 0, 0.06, _hz(76), 'cuadrada', 0.16); s.tono(b, 0.06, 0.1, _hz(83), 'cuadrada', 0.16); e['ok'] = b
    b = s.lienzo(0.25); s.tono(b, 0, 0.08, 880, 'cuadrada', 0.12); s.tono(b, 0.12, 0.08, 880, 'cuadrada', 0.12); e['alarma'] = b
    b = s.lienzo(0.45); s.ruido(b, 0, 0.45, 0.32, paso=2); s.tono(b, 0, 0.3, 600, 'cuadrada', 0.1, hz_fin=80); e['destruir'] = b
    return e


GANANCIA_MUSICA = {'menu': 0.9, 'carrera': 0.85}


def componer_todo(s, avisar=lambda f, m: None):
    """Genera todos los sonidos del juego: {'efectos': {...}, 'jingles': {...}, 'musicas': {...}}."""
    avisar(0.05, "EFECTOS DE SONIDO")
    efectos = crear_efectos(s)
    avisar(0.15, "FANFARRIAS")
    jingles = crear_jingles(s)
    avisar(0.3, "COMPONIENDO MÚSICA DEL MENÚ")
    menu = componer_menu(s)
    avisar(0.6, "COMPONIENDO MÚSICA DE CARRERA")
    carrera = componer_carrera(s)
    return {"efectos": efectos, "jingles": jingles, "musicas": {"menu": menu, "carrera": carrera}}


# ---------------------------------------------------------------------
#  Gestor
# ---------------------------------------------------------------------
class GestorAudio:
    """Fachada de audio. Si no hay tarjeta de sonido, todos los métodos simplemente no hacen nada."""

    VOL_MUSICA = 0.55

    def __init__(self):
        self._ok = pygame.mixer.get_init() is not None
        self._silencio = False
        self._efectos, self._jingles, self._musicas = {}, {}, {}
        self._actual = None
        self._canal = None
        if self._ok:
            pygame.mixer.set_num_channels(12)
            pygame.mixer.set_reserved(1)
            self._canal = pygame.mixer.Channel(0)

    @property
    def silenciado(self):
        return self._silencio

    def cargar(self, avisar):
        """Carga los .ogg pregenerados (rápido, ideal para el navegador) o sintetiza todo."""
        if not self._ok:
            avisar(1.0, "SIN DISPOSITIVO DE AUDIO")
            return
        try:
            if not self._cargar_archivos(avisar):
                freq, _formato, canales = pygame.mixer.get_init()
                s = Sintetizador(freq)
                todo = componer_todo(s, avisar)
                self._efectos = {n: s.a_sonido(b, canales) for n, b in todo["efectos"].items()}
                self._jingles = {n: s.a_sonido(b, canales) for n, b in todo["jingles"].items()}
                self._musicas = {n: s.a_sonido(b, canales, GANANCIA_MUSICA[n]) for n, b in todo["musicas"].items()}
            avisar(1.0, "¡LISTO!")
        except (pygame.error, ValueError, MemoryError):
            self._ok = False

    def _cargar_archivos(self, avisar):
        import json
        import os
        from . import config as C
        indice = os.path.join(C.DIR_AUDIO, "indice.json")
        if not os.path.isfile(indice):
            return False
        with open(indice, encoding="utf-8") as f:
            grupos = json.load(f)
        destinos = {"efectos": self._efectos, "jingles": self._jingles, "musicas": self._musicas}
        total = sum(len(v) for v in grupos.values())
        hechos = 0
        for grupo, nombres in grupos.items():
            for nombre in nombres:
                destinos[grupo][nombre] = pygame.mixer.Sound(os.path.join(C.DIR_AUDIO, f"{nombre}.ogg"))
                hechos += 1
                avisar(hechos / total, "CARGANDO SONIDOS")
        return True

    def musica(self, nombre):
        if not self._ok or nombre == self._actual:
            return
        self._actual = nombre
        self._canal.stop()
        self._canal.unpause()
        if nombre and not self._silencio and nombre in self._musicas:
            self._canal.play(self._musicas[nombre], loops=-1)
            self._canal.set_volume(self.VOL_MUSICA)

    def jingle(self, nombre):
        if not self._ok:
            return
        self._actual = None
        self._canal.stop()
        if not self._silencio and nombre in self._jingles:
            self._canal.play(self._jingles[nombre])
            self._canal.set_volume(0.8)

    def efecto(self, nombre):
        if self._ok and not self._silencio and nombre in self._efectos:
            self._efectos[nombre].play()

    def pausar(self):
        if self._ok:
            self._canal.pause()

    def reanudar(self):
        if self._ok:
            self._canal.unpause()

    def alternar_silencio(self):
        if not self._ok:
            return
        self._silencio = not self._silencio
        if self._silencio:
            self._canal.stop()
        else:
            actual, self._actual = self._actual, None
            self.musica(actual)
