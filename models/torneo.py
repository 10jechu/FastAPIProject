from pydantic import BaseModel
from typing import Optional

class Torneo(BaseModel):
    id: str
    nombre: str
    anio: int
    pais_anfitrion: Optional[str] = None
    estado: str
    eliminado: str

    class Config:
        arbitrary_types_allowed = True