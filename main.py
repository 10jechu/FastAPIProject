from typing import List
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from datetime import date
import pandas as pd
import logging

# Importar modelos y utilidades
from models.equipo import Equipo
from models.jugador import Jugador
from models.partido import Partido
from models.torneo import Torneo
from models.plantilla import Plantilla
from utils.csv_handler import CSVHandler
from utils.exceptions import NotFoundException, DuplicateException

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
        self.df = pd.read_csv("data/equipos.csv")

    def get_all(self) -> List[Equipo]:
        return [Equipo(
            str(row["id"]),
            row["nombre"],
            row["pais"],
            int(row["enfrentamientos_con_colombia"])
        ) for _, row in self.df.iterrows()]

class JugadorOps:
    def __init__(self, csv_file: str):
        self.csv_handler = CSVHandler(csv_file)

    def get_all(self) -> List[Jugador]:
        """Obtener todos los jugadores desde el archivo CSV."""
        try:
            jugadores = self.csv_handler.read_all(Jugador)
            logger.info(f"Loaded {len(jugadores)} jugadores from {self.csv_handler.file_path}")
            return jugadores
        except Exception as e:
            logger.error(f"Error loading jugadores: {str(e)}", exc_info=True)
            raise RuntimeError(f"Error al cargar jugadores: {str(e)}") from e

    def get_by_id(self, jugador_id: int) -> Jugador:
        """Obtener un jugador por su ID."""
        try:
            jugadores = self.get_all()
            for jugador in jugadores:
                if jugador.id == jugador_id:
                    return jugador
            logger.warning(f"Jugador with ID {jugador_id} not found")
            raise NotFoundException("Jugador", jugador_id)
        except NotFoundException:
            raise
        except Exception as e:
            logger.error(f"Error in get_by_id for {jugador_id}: {str(e)}", exc_info=True)
            raise RuntimeError(f"Error al obtener jugador {jugador_id}: {str(e)}") from e

    def get_by_year(self, year: int) -> List[Jugador]:
        """Obtener jugadores por año."""
        try:
            jugadores = self.get_all()
            filtered_jugadores = [jugador for jugador in jugadores if jugador.año == year]
            if not filtered_jugadores:
                logger.info(f"No jugadores found for year {year}")
            return filtered_jugadores
        except Exception as e:
            logger.error(f"Error in get_by_year for {year}: {str(e)}", exc_info=True)
            raise RuntimeError(f"Error al filtrar jugadores por año {year}: {str(e)}") from e

    def create(self, jugador: Jugador) -> Jugador:
        """Crear un nuevo jugador."""
        try:
            jugadores = self.get_all()
            for existing in jugadores:
                if existing.id == jugador.id:
                    raise DuplicateException("Jugador", jugador.id)
            jugadores.append(jugador)
            self.csv_handler.write_all([j.model_dump() for j in jugadores])
            logger.info(f"Created jugador with ID {jugador.id}")
            return jugador
        except DuplicateException:
            raise
        except Exception as e:
            logger.error(f"Error creating jugador: {str(e)}", exc_info=True)
            raise RuntimeError(f"Error al crear jugador: {str(e)}") from e

    def update(self, jugador_id: int, updated_jugador: Jugador) -> Jugador:
        """Actualizar un jugador existente."""
        try:
            jugadores = self.get_all()
            for i, jugador in enumerate(jugadores):
                if jugador.id == jugador_id:
                    updated_jugador.id = jugador_id
                    jugadores[i] = updated_jugador
                    self.csv_handler.write_all([j.model_dump() for j in jugadores])
                    logger.info(f"Updated jugador with ID {jugador_id}")
                    return updated_jugador
            raise NotFoundException("Jugador", jugador_id)
        except NotFoundException:
            raise
        except Exception as e:
            logger.error(f"Error updating jugador {jugador_id}: {str(e)}", exc_info=True)
            raise RuntimeError(f"Error al actualizar jugador {jugador_id}: {str(e)}") from e

    def delete(self, jugador_id: int) -> None:
        """Eliminar un jugador por su ID."""
        try:
            jugadores = self.get_all()
            for i, jugador in enumerate(jugadores):
                if jugador.id == jugador_id:
                    jugadores.pop(i)
                    self.csv_handler.write_all([j.model_dump() for j in jugadores])
                    logger.info(f"Deleted jugador with ID {jugador_id}")
                    return
            raise NotFoundException("Jugador", jugador_id)
        except NotFoundException:
            raise
        except Exception as e:
            logger.error(f"Error deleting jugador {jugador_id}: {str(e)}", exc_info=True)
            raise RuntimeError(f"Error al eliminar jugador {jugador_id}: {str(e)}") from e

    def toggle_active(self, jugador_id: int) -> Jugador:
        """Alternar el estado activo de un jugador."""
        try:
            jugadores = self.get_all()
            for i, jugador in enumerate(jugadores):
                if jugador.id == jugador_id:
                    jugador.activo = not jugador.activo
                    jugadores[i] = jugador
                    self.csv_handler.write_all([j.model_dump() for j in jugadores])
                    logger.info(f"Toggled active status for jugador {jugador_id}")
                    return jugador
            raise NotFoundException("Jugador", jugador_id)
        except NotFoundException:
            raise
        except Exception as e:
            logger.error(f"Error toggling active for {jugador_id}: {str(e)}", exc_info=True)
            raise RuntimeError(f"Error al alternar estado de jugador {jugador_id}: {str(e)}") from e

    def get_jugador_status(self, jugador_id: int) -> dict:
        """Obtener el estado de un jugador."""
        try:
            jugador = self.get_by_id(jugador_id)
            return {
                "id": jugador.id,
                "nombre": jugador.nombre,
                "activo": jugador.activo,
                "estado": "activo" if jugador.activo else "inactivo"
            }
        except NotFoundException as e:
            raise
        except Exception as e:
            logger.error(f"Error getting status for {jugador_id}: {str(e)}", exc_info=True)
            raise RuntimeError(f"Error al obtener estado de jugador {jugador_id}: {str(e)}") from e

class PartidoOps:
    def __init__(self):
        self.df = pd.read_csv("data/partidos.csv")

    def get_all(self) -> List[Partido]:
        return [Partido(
            str(row["id"]),
            row["equipo_local"],
            row["equipo_visitante"],
            pd.to_datetime(row["fecha"]).date(),
            int(row["goles_local"]),
            int(row["goles_visitante"]),
            int(row["torneo_id"])
        ) for _, row in self.df.iterrows()]

    def get_by_year(self, year: int) -> List[Partido]:
        return [partido for partido in self.get_all() if partido.fecha.year == year]

class TorneoOps:
    def __init__(self):
        self.df = pd.read_csv("data/torneos.csv")

    def get_all(self) -> List[Torneo]:
        return [Torneo(
            str(row["id"]),
            row["nombre"],
            int(row["anio"]),
            row["pais_anfitrion"],
            row["estado"],
            row["eliminado"]
        ) for _, row in self.df.iterrows()]

class PlantillaOps:
    def __init__(self):
        self.df = pd.read_csv("data/plantilla.csv")

    def get_all(self) -> List[Plantilla]:
        return [Plantilla(
            str(row["id"]),
            str(row["equipo_id"]),
            row["nombre"],
            row["posicion"],
            int(row["año"])
        ) for _, row in self.df.iterrows()]

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
        jugadores = jugador_ops.get_all() if not ano else jugador_ops.get_by_year(ano)
        return templates.TemplateResponse("jugadores.html", {"request": request, "jugadores": jugadores})
    except Exception as e:
        logger.error(f"Error in get_jugadores: {str(e)}", exc_info=True)
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
        partidos = partido_ops.get_all() if not ano else partido_ops.get_by_year(ano)
        if not partidos:
            return templates.TemplateResponse(
                "estadisticas.html",
                {"request": request, "estadisticas": {"message": f"No se encontraron partidos para el año {ano}"}}
            )
        total_partidos = len(partidos)
        goles_anotados = sum(p.goles_local for p in partidos if p.equipo_local.lower() == "colombia") + \
                         sum(p.goles_visitante for p in partidos if p.equipo_visitante.lower() == "colombia")
        goles_recibidos = sum(p.goles_visitante for p in partidos if p.equipo_local.lower() == "colombia") + \
                          sum(p.goles_local for p in partidos if p.equipo_visitante.lower() == "colombia")
        victorias = sum(1 for p in partidos if (p.equipo_local.lower() == "colombia" and p.goles_local > p.goles_visitante) or
                        (p.equipo_visitante.lower() == "colombia" and p.goles_visitante > p.goles_local))
        empates = sum(1 for p in partidos if ((p.equipo_local.lower() == "colombia" or p.equipo_visitante.lower() == "colombia") and
                                              p.goles_local == p.goles_visitante))
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