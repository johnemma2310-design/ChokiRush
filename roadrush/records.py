"""Récords locales (en el equipo o en el navegador) y servicio de clasificación en línea."""


class GestorRecords:
    """Top 5 local. Se guarda en un `Almacen` (archivo JSON o localStorage)."""
    MAXIMO = 5
    CLAVE = "records"

    def __init__(self, almacen):
        self._almacen = almacen
        self._lista = self._cargar()

    def _cargar(self):
        datos = self._almacen.leer(self.CLAVE, [])
        lista = []
        for d in datos if isinstance(datos, list) else []:
            try:
                lista.append({"nombre": str(d["nombre"])[:10], "puntos": int(d["puntos"]),
                              "nivel": int(d.get("nivel", 1)), "dificultad": str(d.get("dificultad", "normal")),
                              "piloto": d.get("piloto")})
            except (KeyError, TypeError, ValueError):
                continue
        lista.sort(key=lambda d: d["puntos"], reverse=True)
        return lista[:self.MAXIMO]

    @property
    def lista(self):
        return tuple(dict(d) for d in self._lista)

    @property
    def mejor(self):
        return self._lista[0]["puntos"] if self._lista else 0

    def califica(self, puntos):
        if puntos <= 0:
            return False
        return len(self._lista) < self.MAXIMO or puntos > self._lista[-1]["puntos"]

    def agregar(self, entrada):
        """Inserta la entrada (mismo formato que se envía en línea) si entra al top."""
        if not self.califica(entrada["puntos"]):
            return None
        entrada = dict(entrada)
        self._lista.append(entrada)
        self._lista.sort(key=lambda d: d["puntos"], reverse=True)
        self._lista = self._lista[:self.MAXIMO]
        self._almacen.escribir(self.CLAVE, self._lista)
        return self._lista.index(entrada) if entrada in self._lista else None


class ServicioPuntajes:
    """Habla con la API /api/puntajes. Usa cualquier `ClienteRed` (web, escritorio o desconectado)."""

    def __init__(self, cliente):
        self._cliente = cliente

    @property
    def disponible(self):
        return self._cliente.conectado

    def actualizar(self):
        self._cliente.actualizar()

    def enviar(self, entrada):
        return self._cliente.enviar("POST", "/puntajes", entrada)

    def top(self, limite=5, dificultad=None):
        ruta = f"/puntajes?limite={int(limite)}"
        if dificultad:
            ruta += f"&dificultad={dificultad}"
        return self._cliente.enviar("GET", ruta)
