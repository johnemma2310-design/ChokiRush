"""Niveles de dificultad: modifican tráfico, gasolina, choques y puntos."""
from dataclasses import dataclass


@dataclass(frozen=True)
class Dificultad:
    clave: str
    nombre: str
    descripcion: str
    color: tuple
    factor_trafico: float       # multiplica la distancia entre autos (más alto = menos tráfico)
    factor_consumo: float       # multiplica el gasto de gasolina
    costo_choque: float         # gasolina que se pierde al chocar
    factor_puntos: float        # multiplica todos los puntos ganados
    factor_vel_enemigos: float  # multiplica la velocidad del tráfico


DIFICULTADES = (
    Dificultad("facil", "FÁCIL", "Poco tráfico y la gasolina rinde más.", (90, 224, 110),
               factor_trafico=1.45, factor_consumo=0.8, costo_choque=5,
               factor_puntos=0.75, factor_vel_enemigos=0.9),
    Dificultad("normal", "NORMAL", "La experiencia equilibrada.", (255, 214, 64),
               factor_trafico=1.0, factor_consumo=1.0, costo_choque=8,
               factor_puntos=1.0, factor_vel_enemigos=1.0),
    Dificultad("dificil", "DIFÍCIL", "Tráfico pesado, gasolina escasa. ¡Puntos x1.5!", (236, 64, 64),
               factor_trafico=0.72, factor_consumo=1.2, costo_choque=12,
               factor_puntos=1.5, factor_vel_enemigos=1.12),
)

POR_CLAVE = {d.clave: d for d in DIFICULTADES}
