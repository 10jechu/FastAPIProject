from typing import List
from models.equipo import Equipo
from utils.csv_handler import CSVHandler
from utils.exceptions import NotFoundException, DuplicateException

class EquipoOps:
    def __init__(self, csv_file: str):
        self.csv_handler = CSVHandler(csv_file)

    def get_all(self) -> List[Equipo]:
        return self.csv_handler.read_all(Equipo)

    def get_by_id(self, equipo_id: str) -> Equipo:
        equipos = self.get_all()
        for equipo in equipos:
            if equipo.id == equipo_id:
                return equipo
        raise NotFoundException("Equipo", equipo_id)

    def create(self, equipo: Equipo) -> Equipo:
        equipos = self.get_all()
        for existing in equipos:
            if existing.id == equipo.id:
                raise DuplicateException("Equipo", equipo.id)
        equipos.append(equipo)
        self.csv_handler.write_all([equipo.dict() for equipo in equipos])
        return equipo

    def update(self, equipo_id: str, updated_equipo: Equipo) -> Equipo:
        equipos = self.get_all()
        for i, equipo in enumerate(equipos):
            if equipo.id == equipo_id:
                updated_equipo.id = equipo_id
                equipos[i] = updated_equipo
                self.csv_handler.write_all([e.dict() for e in equipos])
                return updated_equipo
        raise NotFoundException("Equipo", equipo_id)

    def delete(self, equipo_id: str) -> None:
        equipos = self.get_all()
        for i, equipo in enumerate(equipos):
            if equipo.id == equipo_id:
                equipos.pop(i)
                self.csv_handler.write_all([e.dict() for e in equipos])
                return
        raise NotFoundException("Equipo", equipo_id)