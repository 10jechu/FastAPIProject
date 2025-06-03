from pydantic import BaseModel
from typing import Optional

class Plantilla(BaseModel):
    id: str
    equipo_id: str
    nombre: Optional[str] = None
    posicion: Optional[str] = None
    año: int

    class Config:
        arbitrary_types_allowed = True