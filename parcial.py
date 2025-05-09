from sqlmodel import SQLModel, Field
from typing import Optional
from datetime import datetime
import enum

# Definimos los estados como Enum
class EstadoTarea(str, enum.Enum):
    PENDIENTE = "Pendiente"
    EN_EJECUCION = "En ejecución"
    REALIZADA = "Realizada"
    CANCELADA = "Cancelada"

class EstadoUsuario(str, enum.Enum):
    ACTIVO = "Activo"
    INACTIVO = "Inactivo"
    ELIMINADO = "Eliminado"

# Modelo de Usuario
class Usuario(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    nombre: str
    email: str
    estado: EstadoUsuario = Field(default=EstadoUsuario.ACTIVO)
    premium: bool = Field(default=False)

# Modelo de Tarea
class Tarea(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    nombre: str
    descripcion: str
    fecha_creacion: datetime = Field(default_factory=datetime.utcnow)
    fecha_modificacion: datetime = Field(default_factory=datetime.utcnow)
    estado: EstadoTarea = Field(default=EstadoTarea.PENDIENTE)
    usuario_id: int = Field(foreign_key="usuario.id")
