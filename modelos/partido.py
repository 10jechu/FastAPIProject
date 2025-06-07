from pydantic import BaseModel
from typing import Optional
from datetime import date

class Partido(BaseModel):
    id: int
    equipo_local: str
    equipo_visitante: str
    fecha: str
    goles_local: int
    goles_visitante: int
    torneo_id: int
    eliminado: str
    tarjetas_amarillas_local: int
    tarjetas_amarillas_visitante: int
    tarjetas_rojas_local: int
    tarjetas_rojas_visitante: int

    class Config:
        arbitrary_types_allowed = True