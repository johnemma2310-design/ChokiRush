// API de clasificación de Choki Rush (función serverless de Vercel + Postgres de Neon).
//   GET  /api/puntajes?limite=5&dificultad=normal&horas=3  -> mejores puntajes (uno por jugador)
//   POST /api/puntajes  {nombre, puntos, nivel, dificultad, piloto} -> guarda y devuelve el puesto
import { neon } from '@neondatabase/serverless';

const sql = neon(process.env.DATABASE_URL);
const DIFICULTADES = new Set(['facil', 'normal', 'dificil']);
const HEX = /^#[0-9a-f]{6}$/i;
const NOMBRE = /^[A-ZÑ0-9 ]{1,10}$/;

function limpiarNombre(texto) {
  return String(texto ?? '').toUpperCase().replace(/[^A-ZÑ0-9 ]/g, '').trim().slice(0, 10);
}

const DIGITOS = '0123456789abcdefghijklmnopqrstuv';   // hasta 32 colores por sprite

function validarSprite(s, maxLado = 24) {
  if (!s || typeof s !== 'object') return null;
  const w = Number(s.w), h = Number(s.h);
  if (!Number.isInteger(w) || !Number.isInteger(h) || w < 1 || h < 1 || w > maxLado || h > maxLado) return null;
  if (!Array.isArray(s.pal) || s.pal.length < 1 || s.pal.length > 32 || !s.pal.every(c => HEX.test(c))) return null;
  const validos = DIGITOS.slice(0, s.pal.length) + '.';
  if (typeof s.px !== 'string' || s.px.length !== w * h || [...s.px].some(c => !validos.includes(c))) return null;
  return { w, h, pal: s.pal.map(c => c.toLowerCase()), px: s.px };
}

function validarEntrada(b) {
  const nombre = limpiarNombre(b?.nombre);
  const puntos = Number(b?.puntos);
  const nivel = Number(b?.nivel);
  if (!NOMBRE.test(nombre)) return { error: 'nombre inválido' };
  if (!Number.isInteger(puntos) || puntos < 0 || puntos > 3000000) return { error: 'puntos inválidos' };
  if (!Number.isInteger(nivel) || nivel < 1 || nivel > 4) return { error: 'nivel inválido' };
  if (!DIFICULTADES.has(b?.dificultad)) return { error: 'dificultad inválida' };
  const p = b?.piloto;
  const sprite = validarSprite(p?.sprite);
  if (!p || !HEX.test(p.color ?? '') || !sprite) return { error: 'piloto inválido' };
  const piloto = { nombre: limpiarNombre(p.nombre) || nombre, color: p.color.toLowerCase(), sprite };
  if (p.retrato) {                       // retrato grande opcional (hasta 256x256)
    const retrato = validarSprite(p.retrato, 256);
    if (!retrato) return { error: 'retrato inválido' };
    piloto.retrato = retrato;
  }
  return { nombre, puntos, nivel, dificultad: b.dificultad, piloto };
}

export default async function handler(req, res) {
  res.setHeader('Access-Control-Allow-Origin', '*');
  res.setHeader('Access-Control-Allow-Headers', 'Content-Type');
  res.setHeader('Access-Control-Allow-Methods', 'GET,POST,OPTIONS');
  res.setHeader('Cache-Control', 'no-store');
  if (req.method === 'OPTIONS') return res.status(204).end();

  try {
    if (req.method === 'GET') {
      const limite = Math.max(1, Math.min(20, parseInt(req.query.limite ?? '5', 10) || 5));
      const dificultad = DIFICULTADES.has(req.query.dificultad) ? req.query.dificultad : null;
      const horas = Math.max(0, Math.min(720, parseFloat(req.query.horas ?? '0') || 0));
      const conRetratos = req.query.retratos === '1';
      const filas = await sql`
        SELECT nombre, puntos, nivel, dificultad,
               CASE WHEN ${conRetratos}::boolean THEN piloto ELSE piloto - 'retrato' END AS piloto, creado FROM (
          SELECT DISTINCT ON (lower(nombre)) nombre, puntos, nivel, dificultad, piloto, creado
          FROM puntajes
          WHERE (${dificultad}::text IS NULL OR dificultad = ${dificultad})
            AND (${horas}::float = 0 OR creado > now() - make_interval(secs => ${horas}::float * 3600))
          ORDER BY lower(nombre), puntos DESC, creado ASC
        ) mejores
        ORDER BY puntos DESC, creado ASC
        LIMIT ${limite}`;
      const total = await sql`SELECT count(DISTINCT lower(nombre))::int AS n FROM puntajes`;
      return res.status(200).json({ puntajes: filas, jugadores: total[0].n });
    }

    if (req.method === 'POST') {
      let cuerpo;
      try {
        cuerpo = typeof req.body === 'string' ? JSON.parse(req.body || '{}') : (req.body ?? {});
      } catch {
        return res.status(400).json({ error: 'JSON inválido' });
      }
      const e = validarEntrada(cuerpo);
      if (e.error) return res.status(400).json({ error: e.error });
      await sql`INSERT INTO puntajes (nombre, puntos, nivel, dificultad, piloto)
                VALUES (${e.nombre}, ${e.puntos}, ${e.nivel}, ${e.dificultad}, ${JSON.stringify(e.piloto)}::jsonb)`;
      const r = await sql`
        SELECT count(*)::int + 1 AS puesto FROM (
          SELECT lower(nombre) AS n, max(puntos) AS m FROM puntajes GROUP BY 1
        ) t WHERE t.m > ${e.puntos} AND t.n <> lower(${e.nombre})`;
      return res.status(201).json({ ok: true, puesto: r[0].puesto });
    }

    return res.status(405).json({ error: 'método no permitido' });
  } catch (err) {
    console.error(err);
    return res.status(500).json({ error: 'error del servidor' });
  }
}
