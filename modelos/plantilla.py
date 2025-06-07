from pydantic import BaseModel
from typing import Optional

class Plantilla(BaseModel):
    id: int
    equipo_id: int
    nombre: Optional[str]
    posicion: Optional[str]
    anio: int
    torneo_id: Optional[int]
    jugador_id: Optional[int]

    class Config:
        arbitrary_types_allowed = True