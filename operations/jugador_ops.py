from typing import List
from models.jugador import Jugador
from utils.csv_handler import CSVHandler
from utils.exceptions import NotFoundException, DuplicateException
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class JugadorOps:
    def __init__(self, csv_file: str):
        self.csv_handler = CSVHandler(csv_file)

    def get_all(self) -> List[Jugador]:
        return self.csv_handler.read_all(Jugador)

    def get_by_id(self, jugador_id: str) -> Jugador:
        jugadores = self.get_all()
        for jugador in jugadores:
            if jugador.id == jugador_id:
                return jugador
        raise NotFoundException("Jugador", jugador_id)

    def get_by_year(self, year: int) -> List[Jugador]:
        jugadores = self.get_all()
        return [jugador for jugador in jugadores if jugador.año == year]

    def create(self, jugador: Jugador) -> Jugador:
        jugadores = self.get_all()
        for existing in jugadores:
            if existing.id == jugador.id:
                raise DuplicateException("Jugador", jugador.id)
        jugadores.append(jugador)
        self.csv_handler.write_all([jugador.model_dump() for jugador in jugadores])
        return jugador

    def update(self, jugador_id: str, updated_jugador: Jugador) -> Jugador:
        jugadores = self.get_all()
        for i, jugador in enumerate(jugadores):
            if jugador.id == jugador_id:
                updated_jugador.id = jugador_id
                jugadores[i] = updated_jugador
                self.csv_handler.write_all([j.model_dump() for j in jugadores])
                return updated_jugador
        raise NotFoundException("Jugador", jugador_id)

    def delete(self, jugador_id: str) -> None:
        jugadores = self.get_all()
        for i, jugador in enumerate(jugadores):
            if jugador.id == jugador_id:
                jugadores.pop(i)
                self.csv_handler.write_all([j.model_dump() for j in jugadores])
                return
        raise NotFoundException("Jugador", jugador_id)

    def toggle_active(self, jugador_id: str) -> Jugador:
        try:
            jugadores = self.get_all()
            for i, jugador in enumerate(jugadores):
                if jugador.id == jugador_id:
                    jugador.activo = not jugador.activo
                    jugadores[i] = jugador
                    self.csv_handler.write_all([j.model_dump() for j in jugadores])
                    return jugador
            raise NotFoundException("Jugador", jugador_id)
        except Exception as e:
            logger.error(f"Error al cambiar estado de jugador {jugador_id}: {str(e)}")
            raise

    def get_jugador_status(self, jugador_id: str) -> dict:
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
            logger.error(f"Error al obtener estado de jugador {jugador_id}: {str(e)}")
            raise
