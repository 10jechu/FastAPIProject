from typing import List, Dict, Any, TypeVar, Type
from datetime import date
import logging
import os
import csv

T = TypeVar('T')

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class CSVHandler:
    def __init__(self, file_path: str):
        self.file_path = file_path
        if not os.path.exists(file_path):
            logger.warning(f"File not found: {file_path}, creating empty file")
            with open(file_path, 'w', newline='', encoding='utf-8') as csvfile:
                pass  # Crea el archivo vacío

    def read_all(self, model: Type[T]) -> List[T]:
        records = []
        try:
            with open(self.file_path, 'r', encoding='utf-8') as csvfile:
                reader = csv.DictReader(csvfile)
                logger.info(f"Headers from {self.file_path}: {reader.fieldnames}")
                for row in reader:
                    logger.debug(f"Raw row from {self.file_path}: {row}")
                    converted_row = self._convert_types(row, model)
                    try:
                        records.append(model(**converted_row))
                    except Exception as e:
                        logger.error(f"Validation error for row {row}: {str(e)}", exc_info=True)
        except FileNotFoundError:
            logger.warning(f"File not found: {self.file_path}, returning empty list")
            return []
        return records

    def write_all(self, records: List[Dict[str, Any]]) -> None:
        if not records:
            logger.warning(f"No records to write to {self.file_path}")
            return
        with open(self.file_path, 'w', newline='', encoding='utf-8') as csvfile:
            fieldnames = records[0].keys() if records else []
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(records)

    def _convert_types(self, row: Dict[str, str], model: Type[T]) -> Dict[str, Any]:
        converted_row = {}
        model_fields = model.__annotations__

        for key, value in row.items():
            expected_type = model_fields.get(key)

            if expected_type is None:
                logger.warning(f"Field {key} in {self.file_path} not found in model {model.__name__}, ignoring")
                continue

            if not value and value != 0:
                if expected_type == int:
                    converted_row[key] = 0
                elif expected_type == bool:
                    converted_row[key] = False
                else:
                    converted_row[key] = None
                continue

            try:
                if expected_type == str:
                    converted_row[key] = value
                elif expected_type == int:
                    converted_row[key] = int(value)
                elif expected_type == date:
                    converted_row[key] = date.fromisoformat(value)
                elif expected_type == bool:
                    converted_row[key] = value.lower() in ('true', '1', 'yes')
                else:
                    converted_row[key] = value
            except ValueError as e:
                logger.error(f"Conversion error for {key}={value} in {self.file_path}: {str(e)}")
                converted_row[key] = None
        return converted_row