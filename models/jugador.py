from pydantic import BaseModel
from typing import Optional

class Jugador(BaseModel):
    id: int
    Jugadores: str
    F_Nacim_Edad: str  # Ejemplo: "31/08/1988 (32)"
    Club: str
    Altura: str  # Ejemplo: "1.83m"
    Pie: str
    Partidos_con_la_seleccion: int
    Goles: int
    Numero_de_camisa: int
    anio: int
    posicion: Optional[str] = None  # Nueva columna para posición
    activo: Optional[bool] = True  # Nueva columna para estado activo

    class Config:
        arbitrary_types_allowed = True