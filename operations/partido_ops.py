from typing import List
from models.partido import Partido
from utils.csv_handler import CSVHandler
from utils.exceptions import NotFoundException, DuplicateException
import logging
from datetime import date

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
                logger.error(f"Error reading partidos from {self.csv_file}: {str(e)}", exc_info=True)
                if "ValidationError" in str(e):
                    logger.error("Validation error details:", exc_info=True)
                raise
        return self._cache

    def _save_data(self, partidos: List[Partido]) -> None:
        try:
            partidos_dicts = []
            for p in partidos:
                p_dict = p.model_dump()
                # Asegurar que fecha se guarde en formato ISO
                p_dict['fecha'] = p_dict['fecha'].isoformat() if p_dict['fecha'] else ''
                # Nota: Si eliminado se cambia a bool en el modelo, convertir "si"/"no" a True/False aquí
                partidos_dicts.append(p_dict)
            self.csv_handler.write_all(partidos_dicts)
            self._cache = partidos
            logger.info(f"Successfully saved {len(partidos)} partidos to {self.csv_file}")
        except Exception as e:
            logger.error(f"Error writing partidos to {self.csv_file}: {str(e)}", exc_info=True)
            raise

    def get_all(self) -> List[Partido]:
        try:
            return self._load_data()
        except Exception as e:
            logger.error(f"Error in get_all: {str(e)}", exc_info=True)
            raise

    def get_by_id(self, partido_id: str) -> Partido:
        try:
            partidos = self._load_data()
            for partido in partidos:
                if partido.id == partido_id:
                    return partido
            raise NotFoundException("Partido", partido_id)
        except NotFoundException as e:
            raise
        except Exception as e:
            logger.error(f"Error in get_by_id for partido_id {partido_id}: {str(e)}", exc_info=True)
            raise

    def get_by_year(self, ano: int) -> List[Partido]:
        try:
            partidos = self._load_data()
            filtered_partidos = [partido for partido in partidos if partido.fecha.year == ano]
            if not filtered_partidos:
                logger.info(f"No partidos found for year {ano}")
            else:
                logger.info(f"Found {len(filtered_partidos)} partidos for year {ano}")
            return filtered_partidos
        except Exception as e:
            logger.error(f"Error in get_by_year for year {ano}: {str(e)}", exc_info=True)
            raise

    def create(self, partido: Partido) -> Partido:
        try:
            partidos = self._load_data()
            for existing in partidos:
                if existing.id == partido.id:
                    raise DuplicateException("Partido", partido.id)
            partidos.append(partido)
            self._save_data(partidos)
            logger.info(f"Created partido with id {partido.id}")
            return partido
        except DuplicateException as e:
            raise
        except Exception as e:
            logger.error(f"Error creating partido with id {partido.id}: {str(e)}", exc_info=True)
            raise

    def update(self, partido_id: str, updated_partido: Partido) -> Partido:
        try:
            partidos = self._load_data()
            for i, partido in enumerate(partidos):
                if partido.id == partido_id:
                    updated_partido.id = partido_id
                    partidos[i] = updated_partido
                    self._save_data(partidos)
                    logger.info(f"Updated partido with id {partido_id}")
                    return updated_partido
            raise NotFoundException("Partido", partido_id)
        except NotFoundException as e:
            raise
        except Exception as e:
            logger.error(f"Error updating partido with id {partido_id}: {str(e)}", exc_info=True)
            raise

    def delete(self, partido_id: str) -> None:
        try:
            partidos = self._load_data()
            for i, partido in enumerate(partidos):
                if partido.id == partido_id:
                    partidos.pop(i)
                    self._save_data(partidos)
                    logger.info(f"Deleted partido with id {partido_id}")
                    return
            raise NotFoundException("Partido", partido_id)
        except NotFoundException as e:
            raise
        except Exception as e:
            logger.error(f"Error deleting partido with id {partido_id}: {str(e)}", exc_info=True)
            raise