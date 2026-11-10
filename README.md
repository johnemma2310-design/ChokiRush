# Choki Rush

Juego de carreras arcade con vista desde arriba, en pixel art, hecho en Python con
Programación Orientada a Objetos. Se juega en el computador **o en el navegador**, con
clasificación en línea (top 5 con podio animado).

**En línea:** https://road-rush-five.vercel.app
- Jugar: https://road-rush-five.vercel.app/juego/
- Podio en vivo para proyectar en el salón: https://road-rush-five.vercel.app/podio.html

## Jugar en el computador

```bash
pip install -r requirements.txt
python main.py
```

## Controles

| Tecla | Acción |
|---|---|
| Flecha arriba / Z / W | Acelerar |
| Flecha abajo / X / S | Frenar |
| Flecha izquierda / derecha (A / D) | Girar |
| P o ESC | Pausa |
| M | Música on/off |
| F11 | Pantalla completa (solo escritorio) |
| Enter / Espacio | Aceptar en menús |

## Novedades

- **Crea tu piloto**: subes una foto y el juego la convierte en pixel art de 16×16 (quita el fondo,
  reduce a 7 colores y le pone contorno). Eliges el color del auto y repartes 8 puntos entre
  velocidad, aceleración, manejo y economía.
- **Dificultad**: Fácil (puntos ×0.75), Normal (×1) y Difícil (×1.5).
- **Clasificación en línea**: al terminar escribes tu nombre y tu puntaje sube a la base de datos.
  El top 5 se muestra en un podio con los muñecos animados (el 1.º salta con corona).
- **Podio proyectable**: página web tipo Kahoot que se actualiza sola cada 3 s, con código QR para entrar
  y filtro "ESTA CLASE" (últimas 3 horas).

## La cara del profe 😎

Guarda una foto del profesor como `assets/profesor.png` (o `.jpg`) y vuelve a construir el juego:
las monedas de puntos usarán su cara pixelada.

## Estructura

```
Road Rush POO/
├── main.py                 punto de entrada (async: funciona en escritorio y navegador)
├── pygbag.ini              qué carpetas NO entran al paquete web
├── assets/                 audio .ogg generado + profesor.png
├── roadrush/               el juego (Python + pygame)
│   ├── juego.py            clase Juego: bucle principal y cambio de escenas
│   ├── escena_base.py      Escena (abstracta), CampoTexto, Podio, FondoAnimado
│   ├── escenas.py          menú, selección, creador, dificultad, clasificación, fin
│   ├── carrera.py          la escena de juego
│   ├── entidades.py        jugador, enemigos, objetos y efectos
│   ├── personajes.py       Personaje y PersonajePersonalizado
│   ├── pixelador.py        foto -> pixel art (k-means) y SpritePixel
│   ├── dificultad.py       Fácil / Normal / Difícil
│   ├── plataforma.py       diferencias escritorio/navegador (almacén, fotos, red)
│   ├── records.py          récords locales + servicio de puntajes en línea
│   ├── audio.py            sintetizador chiptune propio
│   └── ...                 pista, marcador, pixelart, fuente_pixel, ui, config
├── herramientas/
│   ├── generar_audio.py    crea los .ogg (requiere: pip install soundfile numpy)
│   └── construir_web.py    compila con pygbag y copia a web/juego/
└── web/                    sitio de Vercel
    ├── index.html          portada
    ├── podio.html          podio en vivo para proyectar
    ├── muneco.js           dibuja los muñecos en el navegador
    ├── api/puntajes.js     API: GET top / POST puntaje (Postgres en Neon)
    └── juego/              juego compilado por pygbag
```

## Publicar cambios en línea

```bash
pip install pygbag
python herramientas/construir_web.py
cd web
vercel deploy --prod
```

La base de datos es Postgres en Neon (proyecto `road-rush`); la conexión está en la variable de
entorno `DATABASE_URL` del proyecto de Vercel (no está en el código).

## Recursos externos

- **pygame-ce** (LGPL) para el juego y **pygbag** (MIT) para compilarlo a WebAssembly.
- **@neondatabase/serverless** para la API, **Vercel** (hosting) y **Neon** (base de datos).
- Fuente "Press Start 2P" (Google Fonts, OFL) y qrcodejs (MIT) solo en las páginas web.
- Gráficos, fuente del juego, música y efectos: originales, generados por código.
