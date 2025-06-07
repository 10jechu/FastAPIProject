from pydantic import BaseModel
from typing import Optional

class Plantilla(BaseModel):
    id: int
    equipo_id: int
    nombre: Optional[str] = None
    posicion: Optional[str] = None
    anio: int
    torneo_id: Optional[int] = None
    jugador_id: Optional[int] = None

    class Config:
        arbitrary_types_allowed = True