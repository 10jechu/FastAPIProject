from typing import List
from models.plantilla import Plantilla
from utils.csv_handler import CSVHandler
from utils.exceptions import NotFoundException, DuplicateException
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class PlantillaOps:
    def __init__(self, csv_file: str, equipo_ops: 'EquipoOps'):
        self.csv_file = csv_file
        self.csv_handler = CSVHandler(csv_file)
        self._cache = None
        self.equipo_ops = equipo_ops

    def _load_data(self) -> List[Plantilla]:
        if self._cache is None:
            try:
                with open(self.csv_file, mode='r', encoding='utf-8') as file:
                    import csv
                    reader = csv.DictReader(file)
                    raw_data = list(reader)
                    logger.info(f"Datos crudos de {self.csv_file}: {raw_data}")
                self._cache = self.csv_handler.read_all(Plantilla)
                logger.info(f"Se cargaron exitosamente {len(self._cache)} plantillas de {self.csv_file}")
            except Exception as e:
                logger.error(f"Error al leer plantillas de {self.csv_file}: {str(e)}")
                if "ValidationError" in str(e):
                    logger.error("Detalles del error de validación:", exc_info=True)
                raise
        return self._cache

    def _save_data(self, plantillas: List[Plantilla]) -> None:
        try:
            plantillas_dicts = [p.model_dump() for p in plantillas]
            self.csv_handler.write_all(plantillas_dicts)
            self._cache = plantillas
            logger.info(f"Se guardaron {len(plantillas)} plantillas en {self.csv_file}")
        except Exception as e:
            logger.error(f"Error al escribir plantillas en {self.csv_file}: {str(e)}")
            raise

    def get_all(self) -> List[Plantilla]:
        return self._load_data()

    def get_by_id(self, plantilla_id: str) -> Plantilla:
        try:
            plantillas = self._load_data()
            for plantilla in plantillas:
                if plantilla.id == plantilla_id:
                    return plantilla
            raise NotFoundException("Plantilla", plantilla_id)
        except Exception as e:
            logger.error(f"Error en get_by_id para plantilla_id {plantilla_id}: {str(e)}")
            raise

    def create(self, plantilla: Plantilla) -> Plantilla:
        try:
            # Validar equipo_id
            equipo = self.equipo_ops.get_by_id(plantilla.equipo_id)
            if not equipo:
                logger.error(f"Equipo con id {plantilla.equipo_id} no encontrado")
                raise NotFoundException("Equipo", plantilla.equipo_id)

            plantillas = self._load_data()
            for existing in plantillas:
                if existing.id == plantilla.id:
                    raise DuplicateException("Plantilla", plantilla.id)
            plantillas.append(plantilla)
            self._save_data(plantillas)
            logger.info(f"Plantilla creada para equipo {plantilla.equipo_id}: {plantilla}")
            return plantilla
        except Exception as e:
            logger.error(f"Error al crear plantilla: {str(e)}")
            raise

    def update(self, plantilla_id: str, updated_plantilla: Plantilla) -> Plantilla:
        try:
            # Validar equipo_id
            equipo = self.equipo_ops.get_by_id(updated_plantilla.equipo_id)
            if not equipo:
                logger.error(f"Equipo con id {updated_plantilla.equipo_id} no encontrado")
                raise NotFoundException("Equipo", updated_plantilla.equipo_id)

            plantillas = self._load_data()
            for i, plantilla in enumerate(plantillas):
                if plantilla.id == plantilla_id:
                    updated_plantilla.id = plantilla_id
                    plantillas[i] = updated_plantilla
                    self._save_data(plantillas)
                    logger.info(f"Plantilla actualizada con id {plantilla_id}: {updated_plantilla}")
                    return updated_plantilla
            raise NotFoundException("Plantilla", plantilla_id)
        except Exception as e:
            logger.error(f"Error al actualizar plantilla con id {plantilla_id}: {str(e)}")
            raise

    def delete(self, plantilla_id: str) -> None:
        try:
            plantillas = self._load_data()
            for i, plantilla in enumerate(plantillas):
                if plantilla.id == plantilla_id:
                    plantillas.pop(i)
                    self._save_data(plantillas)
                    logger.info(f"Plantilla con id {plantilla_id} eliminada")
                    return
            raise NotFoundException("Plantilla", plantilla_id)
        except Exception as e:
            logger.error(f"Error al eliminar plantilla con id {plantilla_id}: {str(e)}")
            raise

    def get_by_year(self, ano: int) -> List[Plantilla]:
        try:
            plantillas = self._load_data()
            filtered_plantillas = [plantilla for plantilla in plantillas if plantilla.ano == ano]
            if not filtered_plantillas:
                logger.info(f"No se encontraron plantillas para el año {ano}")
            return filtered_plantillas
        except Exception as e:
            logger.error(f"Error al filtrar plantillas por año {ano}: {str(e)}")
            raise