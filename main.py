from typing import List
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from datetime import date
import pandas as pd
import logging
from utils.csv_handler import CSVHandler
from utils.exceptions import NotFoundException, DuplicateException, ValidationException

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI()

# Montar la carpeta static para archivos estáticos
app.mount("/static", StaticFiles(directory="static"), name="static")

# Configurar Jinja2
templates = Jinja2Templates(directory="templates")

# Función para validar años
def validate_year(year: int):
    if year not in range(2021, 2025):
        raise HTTPException(status_code=400, detail="El año debe estar entre 2021 y 2024")

# Clases de Operaciones
class EquipoOps:
    def __init__(self):
        self.csv_handler = CSVHandler("data/equipos.csv")

    def get_all(self) -> List[dict]:
        return self.csv_handler.read_all(Equipo)

class JugadorOps:
    def __init__(self, csv_file: str):
        self.csv_handler = CSVHandler(csv_file)
        self.plantilla_handler = CSVHandler("data/plantilla.csv")

    def get_all(self) -> List[dict]:
        try:
            return self.csv_handler.read_all(Jugador)
        except Exception as e:
            logger.error(f"Error loading jugadores: {str(e)}", exc_info=True)
            raise RuntimeError(f"Error al cargar jugadores: {str(e)}") from e

    def get_by_id(self, jugador_id: int) -> dict:
        try:
            jugadores = self.get_all()
            for jugador in jugadores:
                if int(jugador["id"]) == jugador_id:
                    # Calcular edad aproximada (asumiendo 20 años menos que el año)
                    jugador["edad"] = jugador["año"] - 2000 if jugador["año"] else None
                    # Obtener equipos desde plantilla
                    plantillas = self.plantilla_handler.read_all(Plantilla)
                    equipos = [p["equipo_id"] for p in plantillas if p["nombre"] == jugador["nombre"]]
                    jugador["equipos"] = equipos
                    return jugador
            raise NotFoundException("Jugador", str(jugador_id))
        except NotFoundException:
            raise
        except Exception as e:
            logger.error(f"Error in get_by_id for {jugador_id}: {str(e)}", exc_info=True)
            raise RuntimeError(f"Error al obtener jugador {jugador_id}: {str(e)}") from e

    def get_by_year(self, year: int) -> List[dict]:
        try:
            validate_year(year)
            jugadores = self.get_all()
            return [j for j in jugadores if j["año"] == year]
        except Exception as e:
            logger.error(f"Error in get_by_year for {year}: {str(e)}", exc_info=True)
            raise RuntimeError(f"Error al filtrar jugadores por año {year}: {str(e)}") from e

    def create(self, jugador: dict) -> dict:
        try:
            jugadores = self.get_all()
            for existing in jugadores:
                if int(existing["id"]) == int(jugador["id"]):
                    raise DuplicateException("Jugador", jugador["id"])
            jugadores.append(jugador)
            self.csv_handler.write_all([j for j in jugadores])
            logger.info(f"Created jugador with ID {jugador['id']}")
            return jugador
        except DuplicateException:
            raise
        except Exception as e:
            logger.error(f"Error creating jugador: {str(e)}", exc_info=True)
            raise RuntimeError(f"Error al crear jugador: {str(e)}") from e

    def update(self, jugador_id: int, updated_jugador: dict) -> dict:
        try:
            jugadores = self.get_all()
            for i, jugador in enumerate(jugadores):
                if int(jugador["id"]) == jugador_id:
                    updated_jugador["id"] = str(jugador_id)
                    jugadores[i] = updated_jugador
                    self.csv_handler.write_all([j for j in jugadores])
                    logger.info(f"Updated jugador with ID {jugador_id}")
                    return updated_jugador
            raise NotFoundException("Jugador", str(jugador_id))
        except NotFoundException:
            raise
        except Exception as e:
            logger.error(f"Error updating jugador {jugador_id}: {str(e)}", exc_info=True)
            raise RuntimeError(f"Error al actualizar jugador {jugador_id}: {str(e)}") from e

    def delete(self, jugador_id: int) -> None:
        try:
            jugadores = self.get_all()
            for i, jugador in enumerate(jugadores):
                if int(jugador["id"]) == jugador_id:
                    jugadores.pop(i)
                    self.csv_handler.write_all([j for j in jugadores])
                    logger.info(f"Deleted jugador with ID {jugador_id}")
                    return
            raise NotFoundException("Jugador", str(jugador_id))
        except NotFoundException:
            raise
        except Exception as e:
            logger.error(f"Error deleting jugador {jugador_id}: {str(e)}", exc_info=True)
            raise RuntimeError(f"Error al eliminar jugador {jugador_id}: {str(e)}") from e

class PartidoOps:
    def __init__(self):
        self.csv_handler = CSVHandler("data/partidos.csv")

    def get_all(self) -> List[dict]:
        return self.csv_handler.read_all(Partido)

    def get_by_year(self, year: int) -> List[dict]:
        return [p for p in self.get_all() if p["fecha"].year == year]

class TorneoOps:
    def __init__(self):
        self.csv_handler = CSVHandler("data/torneos.csv")

    def get_all(self) -> List[dict]:
        return self.csv_handler.read_all(Torneo)

class PlantillaOps:
    def __init__(self):
        self.csv_handler = CSVHandler("data/plantilla.csv")

    def get_all(self) -> List[dict]:
        return self.csv_handler.read_all(Plantilla)

# Modelos (definidos aquí temporalmente para compatibilidad)
class Equipo(dict):
    id: str
    nombre: str
    pais: str
    enfrentamientos_con_colombia: int

class Jugador(dict):
    id: str
    numero: int
    nombre: str
    posicion: str
    goles: int
    asistencias: int
    año: int
    activo: bool
    tarjetas_amarillas: int
    tarjetas_rojas: int

class Partido(dict):
    id: str
    equipo_local: str
    equipo_visitante: str
    fecha: date
    goles_local: int
    goles_visitante: int
    torneo_id: int
    eliminado: str
    tarjetas_amarillas_local: int
    tarjetas_amarillas_visitante: int
    tarjetas_rojas_local: int
    tarjetas_rojas_visitante: int

class Torneo(dict):
    id: str
    nombre: str
    anio: int
    pais_anfitrion: str | None = None
    estado: str
    eliminado: str

class Plantilla(dict):
    id: str
    equipo_id: str
    nombre: str | None = None
    posicion: str | None = None
    año: int

# Instancias de las clases de operaciones
equipo_ops = EquipoOps()
jugador_ops = JugadorOps("data/jugadores.csv")
partido_ops = PartidoOps()
torneo_ops = TorneoOps()
plantilla_ops = PlantillaOps()

# Endpoints
@app.get("/", response_class=HTMLResponse)
async def read_index(request: Request):
    try:
        return templates.TemplateResponse("index.html", {"request": request})
    except Exception as e:
        logger.error(f"Error in read_index: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/equipos/", response_class=HTMLResponse)
async def get_equipos(request: Request):
    try:
        equipos = equipo_ops.get_all()
        return templates.TemplateResponse("equipos.html", {"request": request, "equipos": equipos})
    except Exception as e:
        logger.error(f"Error in get_equipos: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/jugadores/", response_class=HTMLResponse)
async def get_jugadores(request: Request, ano: int = None):
    try:
        if ano:
            validate_year(ano)
            jugadores = jugador_ops.get_by_year(ano)
        else:
            jugadores = jugador_ops.get_all()
        return templates.TemplateResponse("jugadores.html", {"request": request, "jugadores": jugadores, "ano": ano})
    except Exception as e:
        logger.error(f"Error in get_jugadores: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/jugadores/{jugador_id}", response_class=HTMLResponse)
async def get_jugador(request: Request, jugador_id: int):
    try:
        jugador = jugador_ops.get_by_id(jugador_id)
        return templates.TemplateResponse("jugador_detalle.html", {"request": request, "jugador": jugador})
    except NotFoundException as e:
        raise HTTPException(status_code=404, detail=str(e.detail))
    except Exception as e:
        logger.error(f"Error in get_jugador: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/partidos/", response_class=HTMLResponse)
async def get_partidos(request: Request):
    try:
        partidos = partido_ops.get_all()
        return templates.TemplateResponse("partidos.html", {"request": request, "partidos": partidos})
    except Exception as e:
        logger.error(f"Error in get_partidos: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/torneos/", response_class=HTMLResponse)
async def get_torneos(request: Request):
    try:
        torneos = torneo_ops.get_all()
        return templates.TemplateResponse("torneos.html", {"request": request, "torneos": torneos})
    except Exception as e:
        logger.error(f"Error in get_torneos: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/plantillas/", response_class=HTMLResponse)
async def get_plantillas(request: Request):
    try:
        plantillas = plantilla_ops.get_all()
        return templates.TemplateResponse("plantillas.html", {"request": request, "plantillas": plantillas})
    except Exception as e:
        logger.error(f"Error in get_plantillas: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/estadisticas/completa/", response_class=HTMLResponse)
async def get_full_stats(request: Request, ano: int = None):
    try:
        if ano:
            validate_year(ano)
            partidos = partido_ops.get_by_year(ano)
        else:
            partidos = partido_ops.get_all()
        if not partidos:
            return templates.TemplateResponse(
                "estadisticas.html",
                {"request": request, "estadisticas": {"message": f"No se encontraron partidos para el año {ano}"}}
            )
        total_partidos = len(partidos)
        goles_anotados = sum(p["goles_local"] for p in partidos if p["equipo_local"].lower() == "colombia") + \
                         sum(p["goles_visitante"] for p in partidos if p["equipo_visitante"].lower() == "colombia")
        goles_recibidos = sum(p["goles_visitante"] for p in partidos if p["equipo_local"].lower() == "colombia") + \
                          sum(p["goles_local"] for p in partidos if p["equipo_visitante"].lower() == "colombia")
        victorias = sum(1 for p in partidos if (p["equipo_local"].lower() == "colombia" and p["goles_local"] > p["goles_visitante"]) or
                        (p["equipo_visitante"].lower() == "colombia" and p["goles_visitante"] > p["goles_local"]))
        empates = sum(1 for p in partidos if ((p["equipo_local"].lower() == "colombia" or p["equipo_visitante"].lower() == "colombia") and
                                              p["goles_local"] == p["goles_visitante"]))
        derrotas = total_partidos - victorias - empates
        promedio_goles = round(goles_anotados / total_partidos, 2) if total_partidos > 0 else 0

        estadisticas = {
            "total_partidos": total_partidos,
            "goles_anotados": goles_anotados,
            "goles_recibidos": goles_recibidos,
            "promedio_goles_por_partido": promedio_goles,
            "victorias": victorias,
            "empates": empates,
            "derrotas": derrotas
        }
        return templates.TemplateResponse("estadisticas.html", {"request": request, "estadisticas": estadisticas})
    except Exception as e:
        logger.error(f"Error in get_full_stats: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))