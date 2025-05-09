from pydantic import BaseModel

class Jugador(BaseModel):
    id: str
    numero: int
    nombre: str
    posicion: str
    goles: int
    asistencias: int
    año: int
    activo: bool = True