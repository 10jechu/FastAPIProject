from typing import List
from models.torneo import Torneo
from utils.csv_handler import CSVHandler
from utils.exceptions import NotFoundException, DuplicateException

class TorneoOps:
    def __init__(self, csv_file: str):
        self.csv_handler = CSVHandler(csv_file)

    def get_all(self) -> List[Torneo]:
        return self.csv_handler.read_all(Torneo)

    def get_by_id(self, torneo_id: str) -> Torneo:
        torneos = self.get_all()
        for torneo in torneos:
            if torneo.id == torneo_id:
                return torneo
        raise NotFoundException("Torneo", torneo_id)

    def create(self, torneo: Torneo) -> Torneo:
        torneos = self.get_all()
        for existing in torneos:
            if existing.id == torneo.id:
                raise DuplicateException("Torneo", torneo.id)
        torneos.append(torneo)
        # Convert model to dict, ensuring all fields are serializable
        self.csv_handler.write_all([torneo.model_dump() for torneo in torneos])
        return torneo

    def update(self, torneo_id: str, updated_torneo: Torneo) -> Torneo:
        torneos = self.get_all()
        for i, torneo in enumerate(torneos):
            if torneo.id == torneo_id:
                updated_torneo.id = torneo_id
                torneos[i] = updated_torneo
                self.csv_handler.write_all([t.model_dump() for t in torneos])
                return updated_torneo
        raise NotFoundException("Torneo", torneo_id)

    def delete(self, torneo_id: str) -> None:
        torneos = self.get_all()
        for i, torneo in enumerate(torneos):
            if torneo.id == torneo_id:
                torneos.pop(i)
                self.csv_handler.write_all([t.model_dump() for t in torneos])
                return
        raise NotFoundException("Torneo", torneo_id)