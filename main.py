from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from datetime import date
import pandas as pd
from typing import List, Dict
import os

app = FastAPI()

# Monta la carpeta static para servir archivos HTML, CSS y JS
app.mount("/static", StaticFiles(directory="static"), name="static")

# Define la ruta raíz para servir index.html
@app.get("/", response_class=FileResponse)
async def read_index():
    return FileResponse("static/index.html")

# Constantes
COLOMBIA_ID = "Colombia"

# Modelos
class Equipo(BaseModel):
    id: str
    nombre: str
    pais: str
    enfrentamientos_con_colombia: int

class Partido(BaseModel):
    id: str
    fecha: date
    equipo_local: str
    equipo_visitante: str
    goles_local: int
    goles_visitante: int
    torneo_id: str
    eliminado: str
    tarjetas_amarillas_local: int = 0
    tarjetas_amarillas_visitante: int = 0
    tarjetas_rojas_local: int = 0
    tarjetas_rojas_visitante: int = 0

class Torneo(BaseModel):
    id: str
    nombre: str
    anio: int
    pais_anfitrion: str
    estado: str
    eliminado: str

class Jugador(BaseModel):
    id: str
    numero: int
    nombre: str
    posicion: str
    goles: int
    asistencias: int
    año: int
    activo: bool
    tarjetas_amarillas: int = 0
    tarjetas_rojas: int = 0
    fecha_nacimiento: date
    equipo: str

class Plantilla(BaseModel):
    id: str
    equipo_id: str
    nombre: str
    posicion: str
    año: int

# Operaciones para leer datos con Pandas
class EquipoOps:
    def get_all(self) -> List[Equipo]:
        df = pd.read_csv("data/equipos.csv")
        equipos = []
        for _, row in df.iterrows():
            equipo = Equipo(
                id=str(row["id"]),
                nombre=row["nombre"],
                pais=row["pais"],
                enfrentamientos_con_colombia=int(row["enfrentamientos_con_colombia"])
            )
            equipos.append(equipo)
        return equipos

class PartidoOps:
    def get_all(self) -> List[Partido]:
        df = pd.read_csv("data/partidos.csv")
        partidos = []
        for _, row in df.iterrows():
            partido = Partido(
                id=str(row["id"]),
                fecha=date.fromisoformat(row["fecha"]),
                equipo_local=row["equipo_local"],
                equipo_visitante=row["equipo_visitante"],
                goles_local=int(row["goles_local"]),
                goles_visitante=int(row["goles_visitante"]),
                torneo_id=row["torneo_id"],
                eliminado=row["eliminado"],
                tarjetas_amarillas_local=int(row["tarjetas_amarillas_local"]),
                tarjetas_amarillas_visitante=int(row["tarjetas_amarillas_visitante"]),
                tarjetas_rojas_local=int(row["tarjetas_rojas_local"]),
                tarjetas_rojas_visitante=int(row["tarjetas_rojas_visitante"])
            )
            partidos.append(partido)
        return partidos

class TorneoOps:
    def get_all(self) -> List[Torneo]:
        torneos = []
        try:
            df = pd.read_csv("data/torneos.csv")
            print("Encabezados de torneos.csv:", df.columns.tolist())  # Log para depurar encabezados
            for _, row in df.iterrows():
                print("Fila de torneos.csv:", row.to_dict())  # Log para depurar cada fila
                # Manejar 'N/A' en pais_anfitrion convirtiéndolo a una cadena vacía si es necesario
                pais_anfitrion = row["pais_anfitrion"] if pd.notna(row["pais_anfitrion"]) else ""
                torneo = Torneo(
                    id=str(row["id"]),
                    nombre=row["nombre"],
                    anio=int(row["anio"]),
                    pais_anfitrion=pais_anfitrion,
                    estado=row["estado"],
                    eliminado=row["eliminado"]
                )
                torneos.append(torneo)
        except FileNotFoundError:
            raise HTTPException(status_code=500, detail="Archivo torneos.csv no encontrado")
        except KeyError as e:
            raise HTTPException(status_code=500, detail=f"Error en torneos.csv: Falta la columna {str(e)}")
        except ValueError as e:
            raise HTTPException(status_code=500, detail=f"Error en torneos.csv: {str(e)}")
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error al leer torneos.csv: {str(e)}")
        return torneos

class JugadorOps:
    def get_all(self) -> List[Jugador]:
        df = pd.read_csv("data/jugadores.csv")
        jugadores = []
        for _, row in df.iterrows():
            jugador = Jugador(
                id=str(row["id"]),
                numero=int(row["numero"]),
                nombre=row["nombre"],
                posicion=row["posicion"],
                goles=int(row["goles"]),
                asistencias=int(row["asistencias"]),
                año=int(row["año"]),
                activo=row["activo"].lower() == "true",
                tarjetas_amarillas=int(row["tarjetas_amarillas"]),
                tarjetas_rojas=int(row["tarjetas_rojas"]),
                fecha_nacimiento=date.fromisoformat(row["fecha_nacimiento"]),
                equipo=row["equipo"]
            )
            jugadores.append(jugador)
        return jugadores

class PlantillaOps:
    def get_all(self) -> List[Plantilla]:
        df = pd.read_csv("data/plantilla.csv")  # Nota: Asegúrate de que el nombre del archivo sea correcto
        plantillas = []
        for _, row in df.iterrows():
            plantilla = Plantilla(
                id=str(row["id"]),
                equipo_id=str(row["equipo_id"]),
                nombre=row["nombre"],
                posicion=row["posicion"],
                año=int(row["año"])
            )
            plantillas.append(plantilla)
        return plantillas

# Instancias de operaciones
equipo_ops = EquipoOps()
partido_ops = PartidoOps()
torneo_ops = TorneoOps()
jugador_ops = JugadorOps()
plantilla_ops = PlantillaOps()

# Validaciones
def validate_year(year: int):
    if year < 2021 or year > 2024:
        raise HTTPException(status_code=400, detail="El año debe estar entre 2021 y 2024")

# Endpoints
@app.get("/equipos/", response_model=List[Equipo])
async def get_equipos():
    return equipo_ops.get_all()

@app.get("/partidos/", response_model=List[Partido])
async def get_partidos():
    return partido_ops.get_all()

@app.get("/torneos/", response_model=List[Torneo])
async def get_torneos():
    return torneo_ops.get_all()

@app.get("/jugadores/", response_model=List[Jugador])
async def get_jugadores(ano: int = None):
    if ano:
        validate_year(ano)
    jugadores = jugador_ops.get_all()
    if ano:
        jugadores = [j for j in jugadores if j.año == ano]
    return jugadores

@app.get("/plantillas/", response_model=List[Plantilla])
async def get_plantillas():
    return plantilla_ops.get_all()

@app.get("/estadisticas/completa/")
async def get_estadisticas_completa(torneo_id: str = None, ano: int = None):
    if ano:
        validate_year(ano)
    partidos = partido_ops.get_all()
    jugadores = jugador_ops.get_all()
    
    print(f"Total partidos cargados: {len(partidos)}")
    for p in partidos:
        print(f"Partido ID: {p.id}, Fecha: {p.fecha}, Año: {p.fecha.year}, Local: {p.equipo_local}, Visitante: {p.equipo_visitante}")

    if torneo_id:
        partidos = [p for p in partidos if p.torneo_id == torneo_id]
    if ano:
        partidos = [p for p in partidos if p.fecha.year == ano]

    print(f"Partidos después del filtro (año={ano}, torneo_id={torneo_id}): {len(partidos)}")

    total_partidos = 0
    goles_anotados = 0
    goles_recibidos = 0
    tarjetas_amarillas_partidos = 0
    tarjetas_rojas_partidos = 0
    victorias = 0
    empates = 0
    derrotas = 0

    for partido in partidos:
        if partido.equipo_local != COLOMBIA_ID and partido.equipo_visitante != COLOMBIA_ID:
            continue
        total_partidos += 1
        if partido.equipo_local == COLOMBIA_ID:
            goles_anotados += partido.goles_local
            goles_recibidos += partido.goles_visitante
            tarjetas_amarillas_partidos += partido.tarjetas_amarillas_local
            tarjetas_rojas_partidos += partido.tarjetas_rojas_local
            if partido.goles_local > partido.goles_visitante:
                victorias += 1
            elif partido.goles_local == partido.goles_visitante:
                empates += 1
            else:
                derrotas += 1
        else:
            goles_anotados += partido.goles_visitante
            goles_recibidos += partido.goles_local
            tarjetas_amarillas_partidos += partido.tarjetas_amarillas_visitante
            tarjetas_rojas_partidos += partido.tarjetas_rojas_visitante
            if partido.goles_visitante > partido.goles_local:
                victorias += 1
            elif partido.goles_visitante == partido.goles_local:
                empates += 1
            else:
                derrotas += 1

    tarjetas_amarillas_jugadores = sum(j.tarjetas_amarillas for j in jugadores if not ano or j.año == ano)
    tarjetas_rojas_jugadores = sum(j.tarjetas_rojas for j in jugadores if not ano or j.año == ano)

    tarjetas_amarillas = tarjetas_amarillas_partidos + tarjetas_amarillas_jugadores
    tarjetas_rojas = tarjetas_rojas_partidos + tarjetas_rojas_jugadores

    if total_partidos == 0:
        return {
            "message": f"No se encontraron partidos para la Selección Colombia con torneo_id={torneo_id} y año={ano}",
            "total_partidos": 0,
            "goles_anotados": 0,
            "goles_recibidos": 0,
            "tarjetas_amarillas": 0,
            "tarjetas_rojas": 0,
            "victorias": 0,
            "empates": 0,
            "derrotas": 0,
            "promedio_goles_por_partido": 0
        }

    promedio_goles = goles_anotados / total_partidos if total_partidos > 0 else 0

    return {
        "total_partidos": total_partidos,
        "goles_anotados": goles_anotados,
        "goles_recibidos": goles_recibidos,
        "tarjetas_amarillas": tarjetas_amarillas,
        "tarjetas_rojas": tarjetas_rojas,
        "victorias": victorias,
        "empates": empates,
        "derrotas": derrotas,
        "promedio_goles_por_partido": round(promedio_goles, 2)
    }