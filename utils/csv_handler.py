import csv
from typing import List, Dict, Any, TypeVar, Type
from datetime import date

T = TypeVar('T')

class CSVHandler:
    def __init__(self, file_path: str):
        self.file_path = file_path

    def read_all(self, model: Type[T]) -> List[T]:
        """Lee todos los registros del CSV y los convierte al modelo especificado."""
        records = []
        try:
            with open(self.file_path, 'r', encoding='utf-8') as file:
                reader = csv.DictReader(file)
                for row in reader:
                    # Convertir tipos según el modelo
                    converted_row = self._convert_types(row, model)
                    records.append(model(**converted_row))
        except FileNotFoundError:
            # Si el archivo no existe, devolver lista vacía
            return []
        return records

    def write_all(self, records: List[Dict[str, Any]]) -> None:
        """Escribe todos los registros en el CSV."""
        if not records:
            return
        with open(self.file_path, 'w', newline='', encoding='utf-8') as file:
            fieldnames = records[0].keys()
            writer = csv.DictWriter(file, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(records)

    def _convert_types(self, row: Dict[str, str], model: Type[T]) -> Dict[str, Any]:
        """Convierte los tipos de los valores del CSV según el modelo."""
        converted_row = {}
        model_fields = model.__annotations__

        for key, value in row.items():
            if not value:
                converted_row[key] = None
                continue

            expected_type = model_fields.get(key)
            if expected_type is None:
                converted_row[key] = value
            elif expected_type == str:
                converted_row[key] = value
            elif expected_type == int:
                converted_row[key] = int(value)
            elif expected_type == date:
                converted_row[key] = date.fromisoformat(value)
            elif expected_type == bool:
                converted_row[key] = value.lower() in ('true', '1', 'yes')
            else:
                converted_row[key] = value
        return converted_row
