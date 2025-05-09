from pydantic import BaseModel
from datetime import date

class Partido(BaseModel):
    id: str
    fecha: date
    equipo_local: str
    equipo_visitante: str
    goles_local: int
    goles_visitante: int
    torneo_id: str
    eliminado: str