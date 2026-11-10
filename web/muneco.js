// Dibuja los muñecos y retratos del juego en un <canvas> (mismas plantillas que roadrush/pixelart.py).
const CONTORNO = '#14141e';
const DIGITOS = '0123456789abcdefghijklmnopqrstuv';

const CUERPOS = [
  ['...KKKKKKKK...', '..KCCCWWCCCK..', '.KCCCCWWCCCCK.', 'KCKCCCWWCCCKCK', 'KCKCCCWWCCCKCK',
   'KSKCCCWWCCCKSK', '.K.KDDDDDDK.K.', '...KDDKKDDK...', '...KDDKKDDK...', '...KDDKKDDK...', '..KKKK..KKKK..'],
  ['...KKKKKKKK...', '..KCCCWWCCCK..', '.KCCCCWWCCCCK.', 'KCKCCCWWCCCKCK', 'KCKCCCWWCCCKCK',
   'KSKCCCWWCCCKSK', '.K.KDDDDDDK.K.', '..KDDK..KDDK..', '..KDDK..KDDK..', '.KDDK....KDDK.', '.KKKK....KKKK.'],
];

const CORONA = ['K..K..K..K', 'KY.KY.KY.K', 'KYYKYYKYYK', 'KYYYRYYYYK', 'KOOOOOOOOK', 'KKKKKKKKKK'];

const CASCO = [
  '....KKKKKK....', '..KKCCCCCCKK..', '.KCCCTTTTCCCK.', '.KCCTTTTTTCCK.', 'KCCCCCCCCCCCCK',
  'KCCKKKKKKKKCCK', 'KCKVVVVVVVVKCK', 'KCKVLVVVVVVKCK', 'KCKVVVVVVVVKCK', 'KCCKKKKKKKKCCK',
  '.KCCCCCCCCCCK.', '.KDCCCCCCCCDK.', '..KDDDDDDDDK..', '...KKKKKKKK...',
];

function oscurecer(hex, k) {
  const n = parseInt(hex.slice(1), 16);
  const c = [(n >> 16) & 255, (n >> 8) & 255, n & 255].map(v => Math.round(v * (1 - k)));
  return '#' + c.map(v => v.toString(16).padStart(2, '0')).join('');
}

function pintarPlantilla(ctx, plantilla, paleta, x, y, e) {
  plantilla.forEach((fila, fy) => {
    [...fila].forEach((ch, fx) => {
      const color = paleta[ch];
      if (color) { ctx.fillStyle = color; ctx.fillRect(x + fx * e, y + fy * e, e, e); }
    });
  });
}

function pintarSprite(ctx, s, x, y, e) {
  for (let i = 0; i < s.px.length; i++) {
    const ch = s.px[i];
    if (ch === '.') continue;
    ctx.fillStyle = s.pal[DIGITOS.indexOf(ch)];
    ctx.fillRect(x + (i % s.w) * e, y + Math.floor(i / s.w) * e, e, e);
  }
}

export function spriteValido(s) {
  return !!s && Number.isInteger(s.w) && Number.isInteger(s.h) && Array.isArray(s.pal) &&
    typeof s.px === 'string' && s.px.length === s.w * s.h;
}

// Convierte un sprite grande (retrato) en un <canvas> a 1x, para dibujarlo escalado sin suavizado.
const cacheRetratos = new WeakMap();
export function lienzoRetrato(s) {
  if (!spriteValido(s)) return null;
  if (cacheRetratos.has(s)) return cacheRetratos.get(s);
  const c = document.createElement('canvas');
  c.width = s.w; c.height = s.h;
  const ctx = c.getContext('2d');
  const img = ctx.createImageData(s.w, s.h);
  const rgb = s.pal.map(h => { const n = parseInt(h.slice(1), 16); return [(n >> 16) & 255, (n >> 8) & 255, n & 255]; });
  for (let i = 0; i < s.px.length; i++) {
    const ch = s.px[i];
    if (ch === '.') continue;
    const [r, g, b] = rgb[DIGITOS.indexOf(ch)];
    img.data.set([r, g, b, 255], i * 4);
  }
  ctx.putImageData(img, 0, 0);
  cacheRetratos.set(s, c);
  return c;
}

// Tamaño del muñeco en pixeles de arte (sin escalar)
export function medidasMuneco(piloto) {
  const s = piloto && spriteValido(piloto.sprite) ? piloto.sprite : { w: 14, h: 14 };
  return { ancho: Math.max(s.w, 14), alto: s.h + CUERPOS[0].length - 1 };
}

// Dibuja el muñeco con su esquina superior izquierda en (x, y), escala e, cuadro de animación 0/1
export function dibujarMuneco(ctx, piloto, x, y, e, cuadro = 0) {
  const color = /^#[0-9a-f]{6}$/i.test(piloto?.color ?? '') ? piloto.color : '#9696a2';
  const { ancho } = medidasMuneco(piloto);
  const cuerpo = CUERPOS[cuadro % 2];
  const pal = { K: CONTORNO, C: color, D: oscurecer(color, 0.45), W: '#fafafa', S: '#f0c496' };
  if (spriteValido(piloto?.sprite)) {
    const s = piloto.sprite;
    pintarPlantilla(ctx, cuerpo, pal, x + ((ancho - 14) >> 1) * e, y + (s.h - 1) * e, e);
    pintarSprite(ctx, s, x + ((ancho - s.w) >> 1) * e, y, e);
  } else {
    pintarPlantilla(ctx, cuerpo, pal, x + ((ancho - 14) >> 1) * e, y + 13 * e, e);
    pintarPlantilla(ctx, CASCO, { K: CONTORNO, C: color, T: '#fafafa', D: oscurecer(color, 0.4), V: '#ffd640', L: '#f0f8ff' },
      x + ((ancho - 14) >> 1) * e, y, e);
  }
}

export function dibujarCorona(ctx, x, y, e) {
  pintarPlantilla(ctx, CORONA, { K: CONTORNO, Y: '#ffd640', O: '#dc9614', R: '#ec4040' }, x, y, e);
}
