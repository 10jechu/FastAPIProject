from typing import List
from models.equipo import Equipo
from utils.csv_handler import CSVHandler
from utils.exceptions import NotFoundException, DuplicateException
import logging

logger = logging.getLogger(__name__)

class EquipoOps:
    def __init__(self, csv_file: str):
        self.csv_handler = CSVHandler(csv_file)

    def get_all(self) -> List[Equipo]:
        try:
            equipos = self.csv_handler.read_all(Equipo)
            logger.info(f"Loaded {len(equipos)} equipos from {self.csv_handler.file_path}")
            return equipos
        except Exception as e:
            logger.error(f"Error loading equipos: {str(e)}")
            raise

    def get_by_id(self, equipo_id: str) -> Equipo:
        equipos = self.get_all()
        for equipo in equipos:
            if str(equipo.id) == str(equipo_id):
                return equipo
        raise NotFoundException("Equipo", equipo_id)

    def create(self, equipo: Equipo) -> Equipo:
        equipos = self.get_all()
        equipo.id = max([e.id for e in equipos] + [0]) + 1 if equipos else 1
        for existing in equipos:
            if str(existing.id) == str(equipo.id):
                raise DuplicateException("Equipo", equipo.id)
        equipos.append(equipo)
        self.csv_handler.write_all([e.model_dump() for e in equipos])
        logger.info(f"Created equipo with ID {equipo.id}")
        return equipo

    def update(self, equipo_id: str, updated_equipo: Equipo) -> Equipo:
        equipos = self.get_all()
        for i, equipo in enumerate(equipos):
            if str(equipo.id) == str(equipo_id):
                updated_equipo.id = int(equipo_id)
                equipos[i] = updated_equipo
                self.csv_handler.write_all([e.model_dump() for e in equipos])
                logger.info(f"Updated equipo with ID {equipo_id}")
                return updated_equipo
        raise NotFoundException("Equipo", equipo_id)

    def delete(self, equipo_id: str) -> None:
        equipos = self.get_all()
        for i, equipo in enumerate(equipos):
            if str(equipo.id) == str(equipo_id):
                equipos.pop(i)
                self.csv_handler.write_all([e.model_dump() for e in equipos])
                logger.info(f"Deleted equipo with ID {equipo_id}")
                return
        raise NotFoundException("Equipo", equipo_id)