    from pydantic import BaseModel

    class Equipo(BaseModel):
        id: int
        nombre: str
        pais: str
        enfrentamientos_con_colombia: int

        class Config:
            arbitrary_types_allowed = True