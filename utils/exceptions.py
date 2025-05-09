from fastapi import HTTPException

class NotFoundException(HTTPException):
    def __init__(self, resource: str, identifier: str):
        super().__init__(status_code=404, detail=f"{resource} con ID {identifier} no encontrado")

class DuplicateException(HTTPException):
    def __init__(self, resource: str, identifier: str):
        super().__init__(status_code=400, detail=f"{resource} con ID {identifier} ya existe")

class ValidationException(HTTPException):
    def __init__(self, detail: str):
        super().__init__(status_code=400, detail=detail)