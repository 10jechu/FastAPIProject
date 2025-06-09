from pydantic import BaseModel
from typing import Optional

class Plantilla(BaseModel):
      id: int  # Cambiado a int para coincidir con plantilla.csv
      equipo_id: int  # Cambiado a int para coincidir con equipos.csv
      nombre: Optional[str] = None
      posicion: Optional[str] = None
      anio: Optional[int] = None
      torneo_id: Optional[int] = None  # Cambiado a int y opcional
      jugador_id: Optional[int] = None  # Cambiado a int y opcional