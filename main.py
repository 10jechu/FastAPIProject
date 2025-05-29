from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
import pandas as pd
from datetime import date
from typing import List
import os

app = FastAPI()

# Configurar Jinja2
templates = Jinja2Templates(directory="templates")

# Constantes
COLOMBIA_ID = "Colombia"

# Modelos
class Equipo:
    def __init__(self, id: str, nombre: str, pais: str, enfrentamientos_con_colombia: int):
        self.id = id
        self.nombre = nombre
        self.pais = pais
        self.enfrentamientos_con_colombia = enfrentamientos_con_colombia

class Partido:
    def __init__(self, id: str, fecha: date, equipo_local: str, equipo_visitante: str, goles_local: int, goles_visitante: int, torneo_id: str, eliminado: str, tarjetas_amarillas_local: int = 0, tarjetas_amarillas_visitante: int = 0, tarjetas_rojas_local: int = 0, tarjetas_rojas_visitante: int = 0):
        self.id = id
        self.fecha = fecha
        self.equipo_local = equipo_local
        self.equipo_visitante = equipo_visitante
        self.goles_local = goles_local
        self.goles_visitante = goles_visitante
        self.torneo_id = torneo_id
        self.eliminado = eliminado
        self.tarjetas_amarillas_local = tarjetas_amarillas_local
        self.tarjetas_amarillas_visitante = tarjetas_amarillas_visitante
        self.tarjetas_rojas_local = tarjetas_rojas_local
        self.tarjetas_rojas_visitante = tarjetas_rojas_visitante

class Torneo:
    def __init__(self, id: str, nombre: str, anio: int, pais_anfitrion: str, estado: str, eliminado: str):
        self.id = id
        self.nombre = nombre
        self.anio = anio
        self.pais_anfitrion = pais_anfitrion
        self.estado = estado
        self.eliminado = eliminado

class Jugador:
    def __init__(self, id: str, numero: int, nombre: str, posicion: str, goles: int, asistencias: int, año: int, activo: bool, fecha_nacimiento: date, equipo: str, tarjetas_amarillas: int = 0, tarjetas_rojas: int = 0):
        self.id = id
        self.numero = numero
        self.nombre = nombre
        self.posicion = posicion
        self.goles = goles
        self.asistencias = asistencias
        self.año = año
        self.activo = activo
        self.tarjetas_amarillas = tarjetas_amarillas
        self.tarjetas_rojas = tarjetas_rojas
        self.fecha_nacimiento = fecha_nacimiento
        self.equipo = equipo

class Plantilla:
    def __init__(self, id: str, equipo_id: str, nombre: str, posicion: str, año: int):
        self.id = id
        self.equipo_id = equipo_id
        self.nombre = nombre
        self.posicion = posicion
        self.año = año

# Operaciones para leer datos con Pandas
class EquipoOps:
    def get_all(self) -> List[Equipo]:
        df = pd.read_csv("data/equipos.csv")
        return [Equipo(str(row["id"]), row["nombre"], row["pais"], int(row["enfrentamientos_con_colombia"])) for _, row in df.iterrows()]

class PartidoOps:
    def get_all(self) -> List[Partido]:
        df = pd.read_csv("data/partidos.csv")
        return [Partido(
            str(row["id"]),
            date.fromisoformat(row["fecha"]),
            row["equipo_local"],
            row["equipo_visitante"],
            int(row["goles_local"]),
            int(row["goles_visitante"]),
            row["torneo_id"],
            row["eliminado"],
            int(row["tarjetas_amarillas_local"]),
            int(row["tarjetas_amarillas_visitante"]),
            int(row["tarjetas_rojas_local"]),
            int(row["tarjetas_rojas_visitante"])
        ) for _, row in df.iterrows()]

class TorneoOps:
    def get_all(self) -> List[Torneo]:
        torneos = []
        try:
            df = pd.read_csv("data/torneos.csv")
            print("Encabezados de torneos.csv:", df.columns.tolist())  # Log para depurar encabezados
            for _, row in df.iterrows():
                print("Fila de torneos.csv:", row.to_dict())  # Log para depurar cada fila
                pais_anfitrion = row["pais_anfitrion"] if pd.notna(row["pais_anfitrion"]) else ""
                torneo = Torneo(
                    str(row["id"]),
                    row["nombre"],
                    int(row["anio"]),
                    pais_anfitrion,
                    row["estado"],
                    row["eliminado"]
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
        return [Jugador(
            str(row["id"]),
            int(row["numero"]),
            row["nombre"],
            row["posicion"],
            int(row["goles"]),
            int(row["asistencias"]),
            int(row["año"]),
            bool(row["activo"]),  # Convertir directamente a booleano
            date.fromisoformat(row["fecha_nacimiento"]),
            row["equipo"],
            int(row["tarjetas_amarillas"]),
            int(row["tarjetas_rojas"])
        ) for _, row in df.iterrows()]

class PlantillaOps:
    def get_all(self) -> List[Plantilla]:
        df = pd.read_csv("data/plantilla.csv")
        return [Plantilla(
            str(row["id"]),
            str(row["equipo_id"]),
            row["nombre"],
            row["posicion"],
            int(row["año"])
        ) for _, row in df.iterrows()]

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
@app.get("/", response_class=HTMLResponse)
async def read_index(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.get("/equipos/", response_class=HTMLResponse)
async def get_equipos(request: Request):
    equipos = equipo_ops.get_all()
    return templates.TemplateResponse("equipos.html", {"request": request, "equipos": equipos})

@app.get("/partidos/", response_class=HTMLResponse)
async def get_partidos(request: Request):
    partidos = partido_ops.get_all()
    return templates.TemplateResponse("partidos.html", {"request": request, "partidos": partidos})

@app.get("/torneos/", response_class=HTMLResponse)
async def get_torneos(request: Request):
    torneos = torneo_ops.get_all()
    return templates.TemplateResponse("torneos.html", {"request": request, "torneos": torneos})

@app.get("/jugadores/", response_class=HTMLResponse)
async def get_jugadores(request: Request, ano: int = None):
    if ano:
        validate_year(ano)
    jugadores = jugador_ops.get_all()
    if ano:
        jugadores = [j for j in jugadores if j.año == ano]
    return templates.TemplateResponse("jugadores.html", {"request": request, "jugadores": jugadores})

@app.get("/plantillas/", response_class=HTMLResponse)
async def get_plantillas(request: Request):
    plantillas = plantilla_ops.get_all()
    return templates.TemplateResponse("plantillas.html", {"request": request, "plantillas": plantillas})

@app.get("/estadisticas/completa/", response_class=HTMLResponse)
async def get_estadisticas_completa(request: Request, torneo_id: str = None, ano: int = None):
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
        estadisticas = {
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
    else:
        promedio_goles = goles_anotados / total_partidos if total_partidos > 0 else 0
        estadisticas = {
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

    return templates.TemplateResponse("estadisticas.html", {"request": request, "estadisticas": estadisticas, "ano": ano, "torneo_id": torneo_id})