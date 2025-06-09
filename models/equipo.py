from pydantic import BaseModel

class Equipo(BaseModel):
      id: int  # Cambiado a int para coincidir con equipos.csv
      nombre: str
      pais: str
      enfrentamientos_con_colombia: int