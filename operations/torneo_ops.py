from typing import List
from models.torneo import Torneo
from utils.csv_handler import CSVHandler
from utils.exceptions import NotFoundException, DuplicateException
import logging

logger = logging.getLogger(__name__)

class TorneoOps:
    def __init__(self, csv_file: str):
        self.csv_handler = CSVHandler(csv_file)

    def get_all(self) -> List[Torneo]:
        try:
            torneos = self.csv_handler.read_all(Torneo)
            logger.info(f"Loaded {len(torneos)} torneos from {self.csv_handler.file_path}")
            return torneos
        except Exception as e:
            logger.error(f"Error loading torneos: {str(e)}")
            raise

    def get_by_id(self, torneo_id: str) -> Torneo:
        torneos = self.get_all()
        for torneo in torneos:
            if str(torneo.id) == str(torneo_id):
                return torneo
        raise NotFoundException("Torneo", torneo_id)

    def create(self, torneo: Torneo) -> Torneo:
        torneos = self.get_all()
        torneo.id = max([t.id for t in torneos] + [0]) + 1 if torneos else 1
        for existing in torneos:
            if str(existing.id) == str(torneo.id):
                raise DuplicateException("Torneo", torneo.id)
        torneos.append(torneo)
        self.csv_handler.write_all([t.model_dump() for t in torneos])
        logger.info(f"Created torneo with ID {torneo.id}")
        return torneo

    def update(self, torneo_id: str, updated_torneo: Torneo) -> Torneo:
        torneos = self.get_all()
        for i, torneo in enumerate(torneos):
            if str(torneo.id) == str(torneo_id):
                updated_torneo.id = int(torneo_id)
                torneos[i] = updated_torneo
                self.csv_handler.write_all([t.model_dump() for t in torneos])
                logger.info(f"Updated torneo with ID {torneo_id}")
                return updated_torneo
        raise NotFoundException("Torneo", torneo_id)

    def delete(self, torneo_id: str) -> None:
        torneos = self.get_all()
        for i, torneo in enumerate(torneos):
            if str(torneo.id) == str(torneo_id):
                torneos.pop(i)
                self.csv_handler.write_all([t.model_dump() for t in torneos])
                logger.info(f"Deleted torneo with ID {torneo_id}")
                return
        raise NotFoundException("Torneo", torneo_id)