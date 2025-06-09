from pydantic import BaseModel
from typing import Optional

class Torneo(BaseModel):
      id: int  # Cambiado a int para coincidir con torneos.csv
      nombre: str
      anio: int
      pais_anfitrion: Optional[str] = None
      estado: str
      eliminado: Optional[str] = None