from pydantic import BaseModel
from typing import Optional

class Partido(BaseModel):
    id: int  # Cambiado a int para coincidir con partidos.csv
    equipo_local: str
    equipo_visitante: str
    fecha: str
    goles_local: int
    goles_visitante: int
    torneo_id: Optional[int] = None  # Cambiado a Optional[int] para manejar casos nulos
    eliminado: Optional[str] = None
    tarjetas_amarillas_local: int
    tarjetas_amarillas_visitante: int
    tarjetas_rojas_local: int
    tarjetas_rojas_visitante: int