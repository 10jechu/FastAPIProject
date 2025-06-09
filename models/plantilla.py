from pydantic import BaseModel

class Plantilla(BaseModel):
    id: int
    equipo_id: int
    nombre: str
    posicion: str
    anio: int
    torneo_id: int
    jugador_id: int