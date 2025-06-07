from pydantic import BaseModel
from typing import Optional

class Equipo(BaseModel):
    id: int
    nombre: str
    pais: str
    enfrentamientos: Optional[int] = 0

    class Config:
        arbitrary_types_allowed = True