from pydantic import BaseModel

class Equipo(BaseModel):
    id: str
    nombre: str
    pais: str
    enfrentamientos_con_colombia: int

    class Config:
        arbitrary_types_allowed = True