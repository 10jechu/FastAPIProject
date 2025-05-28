from pydantic import BaseModel

class Jugador(BaseModel):
    id: int
    numero: int
    nombre: str
    posicion: str
    goles: int
    asistencias: int
    año: int  # O 'ano', dependiendo de cómo lo hayas ajustado
    activo: bool
    tarjetas_amarillas: int = 0
    tarjetas_rojas: int = 0 