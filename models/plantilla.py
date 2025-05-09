from pydantic import BaseModel

class Plantilla(BaseModel):
    id: str
    equipo_id: str
    nombre: str
    posicion: str
    año: int