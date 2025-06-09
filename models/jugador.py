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
    imagen: Optional[str] = None  # Permitir None como valor por defecto