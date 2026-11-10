"""Sistema de puntuación encapsulado."""
from . import config as C


class Marcador:
    """Lleva los puntos. El estado solo cambia mediante métodos que validan las reglas.
    El multiplicador de dificultad se aplica aquí, en un solo lugar."""

    def __init__(self, multiplicador=1.0):
        if multiplicador <= 0:
            raise ValueError("El multiplicador debe ser positivo")
        self._multiplicador = multiplicador
        self._puntos = 0.0
        self._combo = 1
        self._t_combo = 0.0
        self._caras = 0
        self._adelantos = 0
        self._distancia_pendiente = 0.0

    # ---- consultas (solo lectura) ----
    @property
    def puntos(self):
        return int(self._puntos)

    @property
    def multiplicador(self):
        return self._multiplicador

    @property
    def combo(self):
        return self._combo

    @property
    def combo_activo(self):
        return self._combo > 1 and self._t_combo > 0

    @property
    def fraccion_combo(self):
        return max(0.0, self._t_combo / C.T_COMBO)

    @property
    def caras(self):
        return self._caras

    @property
    def adelantos(self):
        return self._adelantos

    # ---- comandos ----
    def sumar(self, cantidad):
        """Suma puntos base (se multiplican por la dificultad). Devuelve lo realmente ganado."""
        if cantidad < 0:
            raise ValueError("El marcador no admite puntos negativos")
        ganados = cantidad * self._multiplicador
        self._puntos += ganados
        return ganados

    def avanzar(self, distancia):
        """10 puntos por cada 100 unidades recorridas."""
        if distancia <= 0:
            return
        self._distancia_pendiente += distancia
        while self._distancia_pendiente >= 100:
            self._distancia_pendiente -= 100
            self.sumar(10)

    def recoger_cara(self, base):
        """Suma una cara del profe aplicando el combo. Devuelve los puntos ganados."""
        self._combo = min(C.COMBO_MAX, self._combo + 1) if self._t_combo > 0 else 1
        self._t_combo = C.T_COMBO
        self._caras += 1
        return int(self.sumar(base * self._combo))

    def registrar_adelanto(self, puntos):
        self._adelantos += 1
        self.sumar(puntos)

    def actualizar(self, dt):
        if self._t_combo > 0:
            self._t_combo -= dt
            if self._t_combo <= 0:
                self._combo = 1
