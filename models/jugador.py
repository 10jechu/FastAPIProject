from pydantic import BaseModel
from typing import Optional

class Jugador(BaseModel):
    id: str
    numero: int
    nombre: str
    posicion: str
    goles: int
    asistencias: int
    año: int
    activo: bool
    tarjetas_amarillas: int
    tarjetas_rojas: int

    class Config:
        arbitrary_types_allowed = True