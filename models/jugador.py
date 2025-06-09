from pydantic import BaseModel, Field
from typing import Optional

class Jugador(BaseModel):
    id: int
    Jugadores: str
    F_Nacim_Edad: str
    Club: str
    Altura: str
    Pie: str
    Partidos_con_la_seleccion: int
    Goles: int
    Numero_de_camisa: int
    anio: int
    posicion: str
    activo: bool
    imagen: Optional[str] = None

    class Config:
        orm_mode = True