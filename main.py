from fastapi import FastAPI, HTTPException
from typing import List
from models.partido import Partido
from models.jugador import Jugador
from models.torneo import Torneo
from models.equipo import Equipo
from models.plantilla import Plantilla
from operations.partido_ops import PartidoOps
from operations.jugador_ops import JugadorOps
from operations.torneo_ops import TorneoOps
from operations.equipo_ops import EquipoOps
from operations.plantilla_ops import PlantillaOps
import os

app = FastAPI()

# Rutas a los CSVs usando rutas relativas al directorio del script
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PARTIDOS_CSV = os.path.join(BASE_DIR, "data", "partidos.csv")
JUGADORES_CSV = os.path.join(BASE_DIR, "data", "jugadores.csv")
TORNEOS_CSV = os.path.join(BASE_DIR, "data", "torneos.csv")
EQUIPOS_CSV = os.path.join(BASE_DIR, "data", "equipos.csv")
PLANTILLAS_CSV = os.path.join(BASE_DIR, "data", "plantillas.csv")

# Instancias de operaciones
partido_ops = PartidoOps(PARTIDOS_CSV)
jugador_ops = JugadorOps(JUGADORES_CSV)
torneo_ops = TorneoOps(TORNEOS_CSV)
equipo_ops = EquipoOps(EQUIPOS_CSV)
plantilla_ops = PlantillaOps(PLANTILLAS_CSV, equipo_ops)  # Añadimos equipo_ops

@app.get("/")
async def root():
    return {"message": "Hola, FastAPI funciona"}

# Endpoints para Partido
@app.get("/partidos/", response_model=List[Partido])
async def get_all_partidos():
    return partido_ops.get_all()

@app.get("/partidos/{partido_id}", response_model=Partido)
async def get_partido(partido_id: str):
    return partido_ops.get_by_id(partido_id)

@app.get("/partidos/filter/{ano}", response_model=List[Partido])
async def get_partidos_by_year(ano: int):
    return partido_ops.get_by_year(ano)

@app.post("/partidos/", response_model=Partido)
async def create_partido(partido: Partido):
    return partido_ops.create(partido)

@app.put("/partidos/{partido_id}", response_model=Partido)
async def update_partido(partido_id: str, partido: Partido):
    return partido_ops.update(partido_id, partido)

@app.delete("/partidos/{partido_id}")
async def delete_partido(partido_id: str):
    partido_ops.delete(partido_id)
    return {"message": f"Partido {partido_id} deleted"}

# Endpoints para Jugador
@app.get("/jugadores/", response_model=List[Jugador])
async def get_all_jugadores():
    return jugador_ops.get_all()

@app.get("/jugadores/filter/{ano}", response_model=List[Jugador])
async def get_jugadores_by_year(ano: int):
    return jugador_ops.get_by_year(ano)

@app.get("/jugadores/{jugador_id}", response_model=Jugador)
async def get_jugador(jugador_id: str):
    return jugador_ops.get_by_id(jugador_id)

@app.post("/jugadores/", response_model=Jugador)
async def create_jugador(jugador: Jugador):
    return jugador_ops.create(jugador)

@app.put("/jugadores/{jugador_id}", response_model=Jugador)
async def update_jugador(jugador_id: str, jugador: Jugador):
    return jugador_ops.update(jugador_id, jugador)

@app.delete("/jugadores/{jugador_id}")
async def delete_jugador(jugador_id: str):
    jugador_ops.delete(jugador_id)
    return {"message": f"Jugador {jugador_id} deleted"}

@app.get("/jugadores/{jugador_id}/status")
async def get_jugador_status(jugador_id: str):
    try:
        return jugador_ops.get_jugador_status(jugador_id)
    except Exception as e:
        raise HTTPException(status_code=404, detail=f"Jugador con id {jugador_id} no encontrado")

@app.patch("/jugadores/{jugador_id}/toggle-active", response_model=Jugador)
async def toggle_jugador_active(jugador_id: str):
    try:
        return jugador_ops.toggle_active(jugador_id)
    except Exception as e:
        raise HTTPException(status_code=404, detail=f"Jugador con id {jugador_id} no encontrado")

# Endpoints para Torneo
@app.get("/torneos/", response_model=List[Torneo])
async def get_all_torneos():
    return torneo_ops.get_all()

@app.get("/torneos/{torneo_id}", response_model=Torneo)
async def get_torneo(torneo_id: str):
    return torneo_ops.get_by_id(torneo_id)

@app.post("/torneos/", response_model=Torneo)
async def create_torneo(torneo: Torneo):
    return torneo_ops.create(torneo)

@app.put("/torneos/{torneo_id}", response_model=Torneo)
async def update_torneo(torneo_id: str, torneo: Torneo):
    return torneo_ops.update(torneo_id, torneo)

@app.delete("/torneos/{torneo_id}")
async def delete_torneo(torneo_id: str):
    torneo_ops.delete(torneo_id)
    return {"message": f"Torneo {torneo_id} deleted"}

# Endpoints para Equipo
@app.get("/equipos/", response_model=List[Equipo])
async def get_all_equipos():
    return equipo_ops.get_all()

@app.get("/equipos/{equipo_id}", response_model=Equipo)
async def get_equipo(equipo_id: str):
    return equipo_ops.get_by_id(equipo_id)

@app.post("/equipos/", response_model=Equipo)
async def create_equipo(equipo: Equipo):
    return equipo_ops.create(equipo)

@app.put("/equipos/{equipo_id}", response_model=Equipo)
async def update_equipo(equipo_id: str, equipo: Equipo):
    return equipo_ops.update(equipo_id, equipo)

@app.delete("/equipos/{equipo_id}")
async def delete_equipo(equipo_id: str):
    equipo_ops.delete(equipo_id)
    return {"message": f"Equipo {equipo_id} deleted"}

# Endpoints para Plantilla
@app.get("/plantillas/", response_model=List[Plantilla])
async def get_all_plantillas():
    return plantilla_ops.get_all()

@app.get("/plantillas/{plantilla_id}", response_model=Plantilla)
async def get_plantilla(plantilla_id: str):
    return plantilla_ops.get_by_id(plantilla_id)

@app.post("/plantillas/", response_model=Plantilla)
async def create_plantilla(plantilla: Plantilla):
    return plantilla_ops.create(plantilla)

@app.put("/plantillas/{plantilla_id}", response_model=Plantilla)
async def update_plantilla(plantilla_id: str, plantilla: Plantilla):
    return plantilla_ops.update(plantilla_id, plantilla)

@app.delete("/plantillas/{plantilla_id}")
async def delete_plantilla(plantilla_id: str):
    plantilla_ops.delete(plantilla_id)
    return {"message": f"Plantilla {plantilla_id} deleted"}