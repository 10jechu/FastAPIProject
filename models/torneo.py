from pydantic import BaseModel

class Torneo(BaseModel):
    id: int
    nombre: str
    anio: int
    pais_anfitrion: str
    estado: str
    eliminado: str