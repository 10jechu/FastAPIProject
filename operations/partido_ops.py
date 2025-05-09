from typing import List
from models.partido import Partido
from utils.csv_handler import CSVHandler
from utils.exceptions import NotFoundException, DuplicateException
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class PartidoOps:
    def __init__(self, csv_file: str):
        self.csv_file = csv_file
        self.csv_handler = CSVHandler(csv_file)
        self._cache = None

    def _load_data(self) -> List[Partido]:
        if self._cache is None:
            try:
                with open(self.csv_file, mode='r', encoding='utf-8') as file:
                    import csv
                    reader = csv.DictReader(file)
                    raw_data = list(reader)
                    logger.info(f"Raw data from {self.csv_file}: {raw_data}")
                self._cache = self.csv_handler.read_all(Partido)
                logger.info(f"Successfully loaded {len(self._cache)} partidos from {self.csv_file}")
            except Exception as e:
                logger.error(f"Error reading partidos from {self.csv_file}: {str(e)}")
                if "ValidationError" in str(e):
                    logger.error("Validation error details:", exc_info=True)
                raise
        return self._cache

    def _save_data(self, partidos: List[Partido]) -> None:
        try:
            partidos_dicts = []
            for p in partidos:
                p_dict = p.model_dump()
                p_dict['fecha'] = p_dict['fecha'].isoformat() if p_dict['fecha'] else ''
                partidos_dicts.append(p_dict)
            self.csv_handler.write_all(partidos_dicts)
            self._cache = partidos
        except Exception as e:
            logger.error(f"Error writing partidos to {self.csv_file}: {str(e)}")
            raise

    def get_all(self) -> List[Partido]:
        return self._load_data()

    def get_by_id(self, partido_id: str) -> Partido:
        try:
            partidos = self._load_data()
            for partido in partidos:
                if partido.id == partido_id:
                    return partido
            raise NotFoundException("Partido", partido_id)
        except Exception as e:
            logger.error(f"Error in get_by_id for partido_id {partido_id}: {str(e)}")
            raise

    def get_by_year(self, ano: int) -> List[Partido]:
        try:
            partidos = self._load_data()
            filtered_partidos = [partido for partido in partidos if partido.fecha.year == ano]
            if not filtered_partidos:
                logger.info(f"No partidos found for year {ano}")
            return filtered_partidos
        except Exception as e:
            logger.error(f"Error in get_by_year for year {ano}: {str(e)}")
            raise

    def create(self, partido: Partido) -> Partido:
        try:
            partidos = self._load_data()
            for existing in partidos:
                if existing.id == partido.id:
                    raise DuplicateException("Partido", partido.id)
            partidos.append(partido)
            self._save_data(partidos)
            return partido
        except Exception as e:
            logger.error(f"Error creating partido: {str(e)}")
            raise

    def update(self, partido_id: str, updated_partido: Partido) -> Partido:
        try:
            partidos = self._load_data()
            for i, partido in enumerate(partidos):
                if partido.id == partido_id:
                    updated_partido.id = partido_id
                    partidos[i] = updated_partido
                    self._save_data(partidos)
                    return updated_partido
            raise NotFoundException("Partido", partido_id)
        except Exception as e:
            logger.error(f"Error updating partido with id {partido_id}: {str(e)}")
            raise

    def delete(self, partido_id: str) -> None:
        try:
            partidos = self._load_data()
            for i, partido in enumerate(partidos):
                if partido.id == partido_id:
                    partidos.pop(i)
                    self._save_data(partidos)
                    return
            raise NotFoundException("Partido", partido_id)
        except Exception as e:
            logger.error(f"Error deleting partido with id {partido_id}: {str(e)}")
            raise
