"""Todo lo que cambia entre escritorio (Windows/Mac/Linux) y navegador (pygbag / WebAssembly).

Cada servicio tiene una clase abstracta y dos implementaciones. El resto del juego solo
conoce la interfaz abstracta, así funciona igual en los dos entornos (polimorfismo).
"""
import base64
import json
import os
import sys
import threading
import urllib.error
import urllib.request
from abc import ABC, abstractmethod

from . import config as C

ES_WEB = sys.platform == "emscripten"


def _ventana():
    import platform  # en pygbag, este módulo expone el objeto `window` del navegador
    return platform.window


# Funciones auxiliares que se inyectan en la página del navegador.
_JS_AYUDA = r"""
window.rrFoto = null;
window.rrElegirFoto = function () {
  window.rrFoto = null;
  const inp = document.createElement('input');
  inp.type = 'file';
  inp.accept = 'image/*';
  inp.oncancel = () => { window.rrFoto = 'CANCEL'; };
  inp.onchange = () => {
    const f = inp.files && inp.files[0];
    if (!f) { window.rrFoto = 'CANCEL'; return; }
    const img = new Image();
    img.onload = () => {
      const s = Math.min(1, 256 / Math.max(img.width, img.height));
      const c = document.createElement('canvas');
      c.width = Math.max(1, Math.round(img.width * s));
      c.height = Math.max(1, Math.round(img.height * s));
      c.getContext('2d').drawImage(img, 0, 0, c.width, c.height);
      window.rrFoto = c.toDataURL('image/png');
    };
    img.onerror = () => { window.rrFoto = 'ERROR'; };
    img.src = URL.createObjectURL(f);
  };
  inp.click();
};
// El selector de archivos solo abre dentro de un gesto real del usuario: por eso se
// dispara aquí, en el keydown del navegador, cuando el juego "arma" el campo FOTO.
window.rrFotoArmada = false;
window.rrArmarFoto = function (v) { window.rrFotoArmada = !!v; };
document.addEventListener('keydown', (e) => {
  if (window.rrFotoArmada && (e.key === 'Enter' || e.key === ' ')) window.rrElegirFoto();
}, true);
document.querySelectorAll('canvas').forEach(c => { c.style.imageRendering = 'pixelated'; });
window.rrTomarFoto = function () { const v = window.rrFoto; if (v !== null) window.rrFoto = null; return v; };
window.rrRed = {};
window.rrPedir = function (id, url, metodo, cuerpo) {
  window.rrRed[id] = null;
  const op = { method: metodo, headers: { 'Content-Type': 'application/json' } };
  if (metodo !== 'GET') op.body = cuerpo;
  fetch(url, op)
    .then(r => r.text().then(t => { window.rrRed[id] = JSON.stringify({ ok: r.ok, status: r.status, texto: t }); }))
    .catch(e => { window.rrRed[id] = JSON.stringify({ ok: false, status: 0, texto: String(e) }); });
};
window.rrTomarRed = function (id) {
  const v = window.rrRed[id];
  if (v === null || v === undefined) return null;
  delete window.rrRed[id];
  return v;
};
"""


def preparar_navegador():
    if ES_WEB:
        _ventana().eval(_JS_AYUDA)


def reportar_error(texto):
    print(texto)
    if ES_WEB:
        try:
            _ventana().console.error("ROADRUSH " + texto)
        except Exception:
            pass


def _texto_js(valor):
    """Convierte un valor devuelto por JavaScript a str de Python (o None)."""
    if valor is None:
        return None
    texto = str(valor)
    return None if texto in ("null", "undefined", "None") else texto


# =====================================================================
#  Almacenamiento persistente
# =====================================================================
class Almacen(ABC):
    @abstractmethod
    def leer(self, clave, defecto=None):
        pass

    @abstractmethod
    def escribir(self, clave, valor):
        pass


class AlmacenArchivo(Almacen):
    """Guarda un diccionario JSON en un archivo (escritorio)."""

    def __init__(self, ruta):
        self._ruta = ruta
        try:
            with open(ruta, encoding="utf-8") as f:
                self._datos = json.load(f)
            if not isinstance(self._datos, dict):
                self._datos = {}
        except (OSError, ValueError):
            self._datos = {}

    def leer(self, clave, defecto=None):
        return json.loads(json.dumps(self._datos.get(clave, defecto)))

    def escribir(self, clave, valor):
        self._datos[clave] = valor
        try:
            with open(self._ruta, "w", encoding="utf-8") as f:
                json.dump(self._datos, f, ensure_ascii=False, indent=1)
        except OSError:
            pass


class AlmacenNavegador(Almacen):
    """Usa localStorage del navegador (persiste entre visitas)."""
    PREFIJO = "roadrush."

    def leer(self, clave, defecto=None):
        try:
            texto = _texto_js(_ventana().localStorage.getItem(self.PREFIJO + clave))
            return defecto if texto is None else json.loads(texto)
        except Exception:
            return defecto

    def escribir(self, clave, valor):
        try:
            _ventana().localStorage.setItem(self.PREFIJO + clave, json.dumps(valor))
        except Exception:
            pass


# =====================================================================
#  Selector de imágenes
# =====================================================================
class SelectorImagen(ABC):
    """abrir() pide una imagen al usuario; resultado() devuelve None mientras espera,
    o una tupla ('ok', bytes, nombre) / ('cancelado', None, '') / ('error', None, mensaje)."""

    @abstractmethod
    def abrir(self):
        pass

    @abstractmethod
    def resultado(self):
        pass

    def armar(self, activo):
        """Avisa que el campo FOTO tiene el foco (solo lo necesita el navegador)."""


class SelectorEscritorio(SelectorImagen):
    def __init__(self):
        self._res = None

    def abrir(self):
        try:
            import tkinter
            from tkinter import filedialog
            raiz = tkinter.Tk()
            raiz.withdraw()
            raiz.attributes("-topmost", True)
            ruta = filedialog.askopenfilename(
                title="Elige la foto de tu piloto",
                filetypes=[("Imágenes", "*.png *.jpg *.jpeg *.bmp *.gif *.webp"), ("Todos", "*.*")])
            raiz.destroy()
        except Exception as e:  # tkinter no disponible
            self._res = ("error", None, str(e))
            return
        if not ruta:
            self._res = ("cancelado", None, "")
            return
        try:
            with open(ruta, "rb") as f:
                self._res = ("ok", f.read(), os.path.basename(ruta))
        except OSError as e:
            self._res = ("error", None, str(e))

    def resultado(self):
        r, self._res = self._res, None
        return r


class SelectorNavegador(SelectorImagen):
    def __init__(self):
        self._esperando = False

    def abrir(self):
        # El selector ya lo abrió JavaScript en el mismo keydown (ver rrFotoArmada).
        self._esperando = True

    def armar(self, activo):
        _ventana().rrArmarFoto(1 if activo else 0)

    def resultado(self):
        if not self._esperando:
            return None
        texto = _texto_js(_ventana().rrTomarFoto())
        if texto is None:
            return None
        self._esperando = False
        if texto == "CANCEL":
            return ("cancelado", None, "")
        if texto.startswith("data:") and "," in texto:
            return ("ok", base64.b64decode(texto.split(",", 1)[1]), "foto.png")
        return ("error", None, "No se pudo leer la imagen")


# =====================================================================
#  Red
# =====================================================================
class Peticion:
    """Resultado de una petición HTTP que llega más tarde (no bloquea el juego)."""

    def __init__(self):
        self.ok = False
        self.estado = 0
        self.datos = None
        self.terminada = False

    def completar(self, ok, estado, texto):
        try:
            self.datos = json.loads(texto) if texto else None
        except ValueError:
            self.datos = None
        self.estado = estado
        self.ok = bool(ok) and self.datos is not None
        self.terminada = True


class ClienteRed(ABC):
    @abstractmethod
    def enviar(self, metodo, ruta, datos=None):
        """Lanza la petición y devuelve una `Peticion`."""

    def actualizar(self):
        """Se llama cada cuadro (solo lo necesita el navegador)."""

    @property
    def conectado(self):
        return True


class ClienteNavegador(ClienteRed):
    def __init__(self, base):
        self._base = base
        self._pendientes = {}
        self._contador = 0

    def enviar(self, metodo, ruta, datos=None):
        self._contador += 1
        ident = f"p{self._contador}"
        pet = Peticion()
        self._pendientes[ident] = pet
        _ventana().rrPedir(ident, self._base + ruta, metodo, json.dumps(datos) if datos is not None else "")
        return pet

    def actualizar(self):
        for ident, pet in list(self._pendientes.items()):
            texto = _texto_js(_ventana().rrTomarRed(ident))
            if texto is not None:
                d = json.loads(texto)
                pet.completar(d.get("ok"), d.get("status", 0), d.get("texto", ""))
                del self._pendientes[ident]


class ClienteEscritorio(ClienteRed):
    """Hace la petición en un hilo para no congelar el juego."""

    def __init__(self, base):
        self._base = base

    def enviar(self, metodo, ruta, datos=None):
        pet = Peticion()
        threading.Thread(target=self._trabajar, args=(pet, metodo, ruta, datos), daemon=True).start()
        return pet

    def _trabajar(self, pet, metodo, ruta, datos):
        cuerpo = json.dumps(datos).encode("utf-8") if datos is not None else None
        req = urllib.request.Request(self._base + ruta, data=cuerpo, method=metodo,
                                     headers={"Content-Type": "application/json", "User-Agent": "RoadRush/1.0"})
        try:
            with urllib.request.urlopen(req, timeout=8) as r:
                pet.completar(True, r.status, r.read().decode("utf-8"))
        except urllib.error.HTTPError as e:
            pet.completar(False, e.code, e.read().decode("utf-8", "replace"))
        except Exception as e:
            pet.completar(False, 0, json.dumps({"error": str(e)}))


class ClienteDesconectado(ClienteRed):
    """Objeto nulo: se usa cuando no hay servidor configurado."""

    def enviar(self, metodo, ruta, datos=None):
        pet = Peticion()
        pet.completar(False, 0, json.dumps({"error": "sin servidor"}))
        return pet

    @property
    def conectado(self):
        return False


def crear_almacen():
    return AlmacenNavegador() if ES_WEB else AlmacenArchivo(C.RUTA_DATOS)


def crear_selector():
    return SelectorNavegador() if ES_WEB else SelectorEscritorio()


def crear_cliente():
    if ES_WEB:
        return ClienteNavegador("/api")
    if C.URL_SERVIDOR:
        return ClienteEscritorio(C.URL_SERVIDOR.rstrip("/") + "/api")
    return ClienteDesconectado()
