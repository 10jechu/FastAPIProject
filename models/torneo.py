from pydantic import BaseModel

class Torneo(BaseModel):
    id: str
    nombre: str
    anio: int
    pais_anfitrion: str
    estado: str
    eliminado: str