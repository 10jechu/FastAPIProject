from typing import List
from models.jugador import Jugador
from utils.csv_handler import CSVHandler
from utils.exceptions import NotFoundException, DuplicateException
import logging

logger = logging.getLogger(__name__)

class JugadorOps:
    def __init__(self, csv_file: str):
        self.csv_handler = CSVHandler(csv_file)

    def get_all(self) -> List[Jugador]:
        try:
            jugadores = self.csv_handler.read_all(Jugador)
            logger.info(f"Loaded {len(jugadores)} jugadores from {self.csv_handler.file_path}")
            return jugadores
        except Exception as e:
            logger.error(f"Error loading jugadores: {str(e)}")
            raise RuntimeError(f"Error al cargar jugadores: {str(e)}") from e

    def get_by_id(self, jugador_id: int) -> Jugador:
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
            logger.error(f"Error in get_by_id for {jugador_id}: {str(e)}")
            raise RuntimeError(f"Error al obtener jugador {jugador_id}: {str(e)}") from e

    def get_by_year(self, year: int) -> List[Jugador]:
        try:
            jugadores = self.get_all()
            filtered_jugadores = [jugador for jugador in jugadores if jugador.anio == year]
            if not filtered_jugadores:
                logger.info(f"No jugadores found for year {year}")
            return filtered_jugadores
        except Exception as e:
            logger.error(f"Error in get_by_year for {year}: {str(e)}")
            raise RuntimeError(f"Error al filtrar jugadores por año {year}: {str(e)}") from e

    def create(self, jugador: Jugador) -> Jugador:
        try:
            jugadores = self.get_all()
            jugador.id = max([j.id for j in jugadores] + [0]) + 1 if jugadores else 1
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
            logger.error(f"Error creating jugador: {str(e)}")
            raise RuntimeError(f"Error al crear jugador: {str(e)}") from e

    def update(self, jugador_id: int, updated_jugador: Jugador) -> Jugador:
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
            logger.error(f"Error updating jugador {jugador_id}: {str(e)}")
            raise RuntimeError(f"Error al actualizar jugador {jugador_id}: {str(e)}") from e

    def delete(self, jugador_id: int) -> None:
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
            logger.error(f"Error deleting jugador {jugador_id}: {str(e)}")
            raise RuntimeError(f"Error al eliminar jugador {jugador_id}: {str(e)}") from e

    def toggle_active(self, jugador_id: int) -> Jugador:
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
            logger.error(f"Error toggling active for {jugador_id}: {str(e)}")
            raise RuntimeError(f"Error al alternar estado de jugador {jugador_id}: {str(e)}") from e

    def get_jugador_status(self, jugador_id: int) -> dict:
        try:
            jugador = self.get_by_id(jugador_id)
            return {
                "id": jugador.id,
                "nombre": jugador.Jugadores,
                "activo": jugador.activo,
                "estado": "activo" if jugador.activo else "inactivo"
            }
        except NotFoundException as e:
            raise
        except Exception as e:
            logger.error(f"Error getting status for {jugador_id}: {str(e)}")
            raise RuntimeError(f"Error al obtener estado de jugador {jugador_id}: {str(e)}") from e