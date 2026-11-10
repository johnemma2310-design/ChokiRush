"""Constantes globales del juego (resolución, rutas, colores y reglas)."""
import os

# --- Pantalla (resolución interna pixel art, se escala automáticamente) ---
ANCHO, ALTO = 320, 240
ANCHO_AREA = 240          # zona de carretera; los 80 px restantes son el HUD
FPS = 60
TITULO = "Choki Rush - La Ruta del Profe"
JUGADOR_Y = 182           # altura fija del auto del jugador en pantalla

# --- Rutas ---
DIR_BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DIR_ASSETS = os.path.join(DIR_BASE, "assets")
RUTAS_FOTO_PROFE = [os.path.join(DIR_ASSETS, n) for n in
                    ("profesor.png", "profesor.jpg", "profesor.jpeg")]
RUTA_PROFE_DIALOGO = os.path.join(DIR_ASSETS, "profesor_dialogo.png")   # cara del profe para diálogos y monedas
RUTA_DATOS = os.path.join(DIR_BASE, "datos_usuario.json")
DIR_AUDIO = os.path.join(DIR_ASSETS, "audio")

# Servidor de clasificación (para la versión de escritorio; en el navegador se usa la misma página).
# Se llena después de publicar en Vercel, p. ej. "https://road-rush.vercel.app"
URL_SERVIDOR = "https://road-rush-five.vercel.app"

# --- Colores ---
NEGRO = (12, 12, 20)
BLANCO = (245, 245, 245)
GRIS = (140, 140, 158)
AMARILLO = (255, 214, 64)
ROJO = (236, 64, 64)
VERDE = (90, 224, 110)
CIAN = (90, 220, 245)
NARANJA = (255, 150, 50)
MORADO = (170, 100, 235)
FONDO_HUD = (22, 20, 38)

# --- Reglas ---
GASOLINA_MAX = 100.0
CONSUMO_BASE = 2.6        # unidades de gasolina por segundo a velocidad máxima
COSTO_CHOQUE = 8.0
GAS_RECARGA = 20.0
T_ESCUDO = 6.0
PUNTOS_CARA = 500
PUNTOS_ADELANTO = 50
PUNTOS_DESTRUIR = 150
PUNTOS_BONO_GAS = 20      # puntos por cada unidad de gasolina sobrante al llegar a la meta
COMBO_MAX = 4
T_COMBO = 3.0
