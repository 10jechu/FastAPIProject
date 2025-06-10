from pydantic import BaseModel

class Equipo(BaseModel):
    id: int
    nombre: str
    pais: str
    enfrentamientos_con_colombia: int
    bandera: Optional[str] = None

    @classmethod
    def validate_bandera(cls, bandera: str) -> Optional[str]:
        if not bandera or pd.isna(bandera):
            return None
        if not bandera.startswith(('http://', 'https://')) and not bandera.endswith('.png'):
            return None
        return bandera