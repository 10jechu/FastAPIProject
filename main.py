from typing import List, Dict
from fastapi import FastAPI, HTTPException, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from datetime import datetime
import logging
import pandas as pd
from pydantic import BaseModel
from models.jugador import Jugador
from models.equipo import Equipo
from models.partido import Partido
from models.plantilla import Plantilla
from models.torneo import Torneo
from utils.csv_handler import CSVHandler
from utils.exceptions import NotFoundException, DuplicateException

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI()

# Montar la carpeta static
app.mount("/static", StaticFiles(directory="static"), name="static")

# Configurar Jinja2
templates = Jinja2Templates(directory="templates")

# Validar años
def validate_year(year: int):
    if year not in range(2021, 2025):
        raise HTTPException(status_code=400, detail="El año debe estar entre 2021 y 2024")

# Extraer edad y fecha de nacimiento
def extract_age(f_nacim_edad: str) -> tuple[str, int]:
    if not f_nacim_edad:
        return "No especificado", None
    try:
        if '(' in f_nacim_edad:
            fecha_str, edad_str = f_nacim_edad.split(' (')
            edad = int(edad_str.replace(')', ''))
            return fecha_str, edad
        return f_nacim_edad, None
    except Exception as e:
        logger.error(f"Error extracting age from {f_nacim_edad}: {str(e)}")
        return f_nacim_edad, None

# Clases de Operaciones con DataFrames precargados
class EquipoOps:
    def __init__(self, csv_file: str, history_file: str = "data/equipos_history.csv"):
        self.csv_file = csv_file
        self.history_file = history_file
        try:
            self.df = pd.read_csv(csv_file)
            expected_columns = ["id", "nombre", "pais", "enfrentamientos_con_colombia"]
            for col in expected_columns:
                if col not in self.df.columns:
                    self.df[col] = None
            self.df['id'] = self.df['id'].astype(str)
            self.df['enfrentamientos_con_colombia'] = self.df['enfrentamientos_con_colombia'].fillna(0).astype(int)
            logger.info(f"Columnas del DataFrame Equipo: {list(self.df.columns)}")
            logger.info(f"Primer registro Equipo: {self.df.iloc[0].to_dict()}")
            if not pd.io.common.file_exists(history_file):
                pd.DataFrame(columns=["id", "nombre", "pais", "enfrentamientos_con_colombia", "action", "timestamp"]).to_csv(history_file, index=False)
        except FileNotFoundError:
            logger.warning(f"File {csv_file} not found, creating empty DataFrame")
            self.df = pd.DataFrame(columns=["id", "nombre", "pais", "enfrentamientos_con_colombia"])
            pd.DataFrame(columns=["id", "nombre", "pais", "enfrentamientos_con_colombia", "action", "timestamp"]).to_csv(history_file, index=False)

    def get_all(self) -> List[dict]:
        equipos = self.df.to_dict(orient='records')
        for equipo in equipos:
            equipo["matches_against_colombia"] = []
            logger.info(f"Equipo procesado: {equipo}")
        return equipos

    def get_by_id(self, equipo_id: str) -> dict:
        try:
            equipo = self.df[self.df["id"] == equipo_id].to_dict(orient='records')
            if not equipo:
                raise NotFoundException("Equipo", equipo_id)
            equipo = equipo[0]
            equipo["matches_against_colombia"] = self.get_matches_against_colombia(equipo["nombre"])
            logger.info(f"Equipo por ID {equipo_id}: {equipo}")
            return equipo
        except NotFoundException:
            raise
        except Exception as e:
            logger.error(f"Error in get_by_id for {equipo_id}: {str(e)}", exc_info=True)
            raise RuntimeError(f"Error al obtener equipo {equipo_id}: {str(e)}") from e

    def create(self, equipo: Equipo) -> dict:
        try:
            if equipo.id in self.df["id"].values:
                raise DuplicateException("Equipo", equipo.id)
            equipo_dict = equipo.dict()
            new_df = pd.DataFrame([equipo_dict])
            self.df = pd.concat([self.df, new_df], ignore_index=True)
            self.df.to_csv(self.csv_file, index=False)
            history_df = pd.DataFrame([{"id": equipo.id, "nombre": equipo.nombre, "pais": equipo.pais, "enfrentamientos_con_colombia": equipo.enfrentamientos_con_colombia, "action": "create", "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")}])
            history_df.to_csv(self.history_file, mode='a', header=False, index=False)
            logger.info(f"Created equipo with ID {equipo.id}")
            return equipo_dict
        except DuplicateException:
            raise
        except Exception as e:
            logger.error(f"Error creating equipo: {str(e)}", exc_info=True)
            raise RuntimeError(f"Error al crear equipo: {str(e)}") from e

    def update(self, equipo_id: str, updated_equipo: Equipo) -> dict:
        try:
            if equipo_id not in self.df["id"].values:
                raise NotFoundException("Equipo", equipo_id)
            original = self.df[self.df["id"] == equipo_id].to_dict(orient='records')[0]
            updated_equipo_dict = updated_equipo.dict()
            updated_equipo_dict["id"] = equipo_id
            self.df.loc[self.df["id"] == equipo_id] = updated_equipo_dict
            self.df.to_csv(self.csv_file, index=False)
            history_df = pd.DataFrame([{"id": equipo_id, "nombre": original["nombre"], "pais": original["pais"], "enfrentamientos_con_colombia": original["enfrentamientos_con_colombia"], "action": "update", "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")}])
            history_df.to_csv(self.history_file, mode='a', header=False, index=False)
            logger.info(f"Updated equipo with ID {equipo_id}")
            return updated_equipo_dict
        except NotFoundException:
            raise
        except Exception as e:
            logger.error(f"Error updating equipo {equipo_id}: {str(e)}", exc_info=True)
            raise RuntimeError(f"Error al actualizar equipo {equipo_id}: {str(e)}") from e

    def delete(self, equipo_id: str) -> None:
        try:
            if equipo_id not in self.df["id"].values:
                raise NotFoundException("Equipo", equipo_id)
            equipo = self.df[self.df["id"] == equipo_id].to_dict(orient='records')[0]
            self.df = self.df[self.df["id"] != equipo_id]
            self.df.to_csv(self.csv_file, index=False)
            history_df = pd.DataFrame([{"id": equipo_id, "nombre": equipo["nombre"], "pais": equipo["pais"], "enfrentamientos_con_colombia": equipo["enfrentamientos_con_colombia"], "action": "delete", "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")}])
            history_df.to_csv(self.history_file, mode='a', header=False, index=False)
            logger.info(f"Deleted equipo with ID {equipo_id}")
        except NotFoundException:
            raise
        except Exception as e:
            logger.error(f"Error deleting equipo {equipo_id}: {str(e)}", exc_info=True)
            raise RuntimeError(f"Error al eliminar equipo {equipo_id}: {str(e)}") from e

    def get_matches_against_colombia(self, equipo_nombre: str) -> List[dict]:
        try:
            partidos_df = pd.read_csv("data/partidos.csv")
            partidos_df['fecha'] = pd.to_datetime(partidos_df['fecha'], errors='coerce')
            matches = partidos_df[
                ((partidos_df['equipo_local'] == equipo_nombre) & (partidos_df['equipo_visitante'] == 'Colombia')) |
                ((partidos_df['equipo_visitante'] == equipo_nombre) & (partidos_df['equipo_local'] == 'Colombia'))
            ].to_dict(orient='records')
            return matches
        except FileNotFoundError:
            logger.warning("File data/partidos.csv not found, returning empty list")
            return []
        except Exception as e:
            logger.error(f"Error getting matches against Colombia: {str(e)}")
            return []

class JugadorOps:
    def __init__(self, csv_file: str, history_file: str = "data/jugadores_history.csv"):
        self.csv_file = csv_file
        self.history_file = history_file
        try:
            self.df = pd.read_csv(csv_file)
            column_mapping = {
                "F. Nacim./Edad": "F_Nacim_Edad",
                "Año": "anio",
                "Posición": "posicion",
                "Partidos con la selección": "Partidos_con_la_seleccion",
                "Numero de camisa": "Numero_de_camisa"
            }
            self.df = self.df.rename(columns=lambda x: column_mapping.get(x, x))
            expected_columns = ["id", "Jugadores", "F_Nacim_Edad", "Club", "Altura", "Pie", "Partidos_con_la_seleccion", "Goles", "Numero_de_camisa", "anio", "posicion", "activo"]
            for col in expected_columns:
                if col not in self.df.columns:
                    self.df[col] = None
            if 'activo' in self.df.columns:
                self.df['activo'] = self.df['activo'].map({'True': True, 'False': False, True: True, False: False}).fillna(True)
            logger.info(f"Columnas del DataFrame: {list(self.df.columns)}")
            logger.info(f"Primer registro: {self.df.iloc[0].to_dict()}")
            if not pd.io.common.file_exists(history_file):
                pd.DataFrame(columns=["id", "Jugadores", "F_Nacim_Edad", "Club", "Altura", "Pie", "Partidos_con_la_seleccion", "Goles", "Numero_de_camisa", "anio", "posicion", "activo", "action", "timestamp"]).to_csv(history_file, index=False)
        except FileNotFoundError:
            logger.warning(f"File {csv_file} not found, creating empty DataFrame")
            self.df = pd.DataFrame(columns=["id", "Jugadores", "F_Nacim_Edad", "Club", "Altura", "Pie", "Partidos_con_la_seleccion", "Goles", "Numero_de_camisa", "anio", "posicion", "activo"])
            pd.DataFrame(columns=["id", "Jugadores", "F_Nacim_Edad", "Club", "Altura", "Pie", "Partidos_con_la_seleccion", "Goles", "Numero_de_camisa", "anio", "posicion", "activo", "action", "timestamp"]).to_csv(history_file, index=False)

    def get_all(self) -> List[dict]:
        return self.df.to_dict(orient='records')

    def get_paginated(self, page: int, per_page: int, anio: int = None) -> tuple[List[dict], int]:
        df = self.df.copy()
        if anio:
            validate_year(anio)
            df = df[df["anio"].astype(int) == anio]
        total = len(df)
        start = (page - 1) * per_page
        end = start + per_page
        jugadores = df.iloc[start:end].to_dict(orient='records')
        for jugador in jugadores:
            jugador["fecha_nacimiento"], jugador["edad"] = extract_age(jugador.get("F_Nacim_Edad", ""))
            if "posicion" in jugador and jugador["posicion"] is None:
                jugador["posicion"] = "No especificado"
            jugador["activo"] = bool(jugador.get("activo", True))
            jugador["Numero_de_camisa"] = jugador.get("Numero_de_camisa", "N/A")
            logger.info(f"Jugador procesado (get_paginated): {jugador}")
        return jugadores, total

    def get_by_id(self, jugador_id: int) -> dict:
        try:
            jugador = self.df[self.df["id"] == jugador_id].to_dict(orient='records')
            if not jugador:
                raise NotFoundException("Jugador", str(jugador_id))
            jugador = jugador[0]
            jugador["fecha_nacimiento"], jugador["edad"] = extract_age(jugador.get("F_Nacim_Edad", ""))
            if "posicion" in jugador and jugador["posicion"] is None:
                jugador["posicion"] = "No especificado"
            jugador["activo"] = bool(jugador.get("activo", True))
            jugador["Numero_de_camisa"] = jugador.get("Numero_de_camisa", "N/A")
            logger.info(f"Jugador por ID {jugador_id} (get_by_id): {jugador}")
            return jugador
        except NotFoundException:
            raise
        except Exception as e:
            logger.error(f"Error in get_by_id for {jugador_id}: {str(e)}", exc_info=True)
            raise RuntimeError(f"Error al obtener jugador {jugador_id}: {str(e)}") from e

    def create(self, jugador: Jugador) -> dict:
        try:
            if jugador.id in self.df["id"].values:
                raise DuplicateException("Jugador", str(jugador.id))
            jugador_dict = jugador.dict()
            new_df = pd.DataFrame([jugador_dict])
            self.df = pd.concat([self.df, new_df], ignore_index=True)
            self.df.to_csv(self.csv_file, index=False)
            history_df = pd.DataFrame([jugador_dict.copy()])
            history_df["action"] = "create"
            history_df["timestamp"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            history_df.to_csv(self.history_file, mode='a', header=False, index=False)
            logger.info(f"Created jugador with ID {jugador.id}")
            return jugador_dict
        except DuplicateException:
            raise
        except Exception as e:
            logger.error(f"Error creating jugador: {str(e)}", exc_info=True)
            raise RuntimeError(f"Error al crear jugador: {str(e)}") from e

    def update(self, jugador_id: int, updated_jugador: Jugador) -> dict:
        try:
            if jugador_id not in self.df["id"].values:
                raise NotFoundException("Jugador", str(jugador_id))
            original = self.df[self.df["id"] == jugador_id].to_dict(orient='records')[0]
            updated_jugador_dict = updated_jugador.dict()
            updated_jugador_dict["id"] = jugador_id
            self.df.loc[self.df["id"] == jugador_id] = updated_jugador_dict
            self.df.to_csv(self.csv_file, index=False)
            history_df = pd.DataFrame([original])
            history_df["action"] = "update"
            history_df["timestamp"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            history_df.to_csv(self.history_file, mode='a', header=False, index=False)
            logger.info(f"Updated jugador with ID {jugador_id}")
            return updated_jugador_dict
        except NotFoundException:
            raise
        except Exception as e:
            logger.error(f"Error updating jugador {jugador_id}: {str(e)}", exc_info=True)
            raise RuntimeError(f"Error al actualizar jugador {jugador_id}: {str(e)}") from e

    def delete(self, jugador_id: int) -> None:
        try:
            if jugador_id not in self.df["id"].values:
                raise NotFoundException("Jugador", str(jugador_id))
            jugador = self.df[self.df["id"] == jugador_id].to_dict(orient='records')[0]
            self.df = self.df[self.df["id"] != jugador_id]
            self.df.to_csv(self.csv_file, index=False)
            history_df = pd.DataFrame([jugador])
            history_df["action"] = "delete"
            history_df["timestamp"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            history_df.to_csv(self.history_file, mode='a', header=False, index=False)
            logger.info(f"Deleted jugador with ID {jugador_id}")
        except NotFoundException:
            raise
        except Exception as e:
            logger.error(f"Error deleting jugador {jugador_id}: {str(e)}", exc_info=True)
            raise RuntimeError(f"Error al eliminar jugador {jugador_id}: {str(e)}") from e

class PartidoOps:
    def __init__(self, csv_file: str, history_file: str = "data/partidos_history.csv"):
        self.csv_file = csv_file
        self.history_file = history_file
        try:
            self.df = pd.read_csv(csv_file)
            self.df['fecha'] = pd.to_datetime(self.df['fecha'], errors='coerce')
            expected_columns = ["id", "fecha", "equipo_local", "equipo_visitante", "goles_local", "goles_visitante", "torneo_id", "eliminado", "tarjetas_amarillas_local", "tarjetas_amarillas_visitante", "tarjetas_rojas_local", "tarjetas_rojas_visitante"]
            for col in expected_columns:
                if col not in self.df.columns:
                    self.df[col] = None
            if not pd.io.common.file_exists(history_file):
                pd.DataFrame(columns=expected_columns + ["action", "timestamp"]).to_csv(history_file, index=False)
        except FileNotFoundError:
            logger.warning(f"File {csv_file} not found, creating empty DataFrame")
            self.df = pd.DataFrame(columns=["id", "fecha", "equipo_local", "equipo_visitante", "goles_local", "goles_visitante", "torneo_id", "eliminado", "tarjetas_amarillas_local", "tarjetas_amarillas_visitante", "tarjetas_rojas_local", "tarjetas_rojas_visitante"])
            pd.DataFrame(columns=["id", "fecha", "equipo_local", "equipo_visitante", "goles_local", "goles_visitante", "torneo_id", "eliminado", "tarjetas_amarillas_local", "tarjetas_amarillas_visitante", "tarjetas_rojas_local", "tarjetas_rojas_visitante", "action", "timestamp"]).to_csv(history_file, index=False)

    def get_all(self) -> List[dict]:
        return self.df.to_dict(orient='records')

    def get_by_id(self, partido_id: str) -> dict:
        try:
            partido = self.df[self.df["id"] == partido_id].to_dict(orient='records')
            if not partido:
                raise NotFoundException("Partido", partido_id)
            return partido[0]
        except NotFoundException:
            raise
        except Exception as e:
            logger.error(f"Error in get_by_id for {partido_id}: {str(e)}")
            raise RuntimeError(f"Error al obtener partido {partido_id}: {str(e)}") from e

    def get_by_year(self, year: int) -> List[dict]:
        try:
            df = self.df.copy()
            df = df[df['fecha'].dt.year == year]
            return df.to_dict(orient='records')
        except Exception as e:
            logger.error(f"Error filtering partidos by year {year}: {str(e)}")
            return []

    def create(self, partido: Partido) -> dict:
        try:
            if partido.id in self.df["id"].values:
                raise DuplicateException("Partido", partido.id)
            partido_dict = partido.dict()
            new_df = pd.DataFrame([partido_dict])
            self.df = pd.concat([self.df, new_df], ignore_index=True)
            self.df.to_csv(self.csv_file, index=False)
            history_df = pd.DataFrame([partido_dict.copy()])
            history_df["action"] = "create"
            history_df["timestamp"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            history_df.to_csv(self.history_file, mode='a', header=False, index=False)
            logger.info(f"Created partido with ID {partido.id}")
            return partido_dict
        except DuplicateException:
            raise
        except Exception as e:
            logger.error(f"Error creating partido: {str(e)}")
            raise RuntimeError(f"Error al crear partido: {str(e)}") from e

    def update(self, partido_id: str, updated_partido: Partido) -> dict:
        try:
            if partido_id not in self.df["id"].values:
                raise NotFoundException("Partido", partido_id)
            original = self.df[self.df["id"] == partido_id].to_dict(orient='records')[0]
            updated_partido_dict = updated_partido.dict()
            updated_partido_dict["id"] = partido_id
            self.df.loc[self.df["id"] == partido_id] = updated_partido_dict
            self.df.to_csv(self.csv_file, index=False)
            history_df = pd.DataFrame([original])
            history_df["action"] = "update"
            history_df["timestamp"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            history_df.to_csv(self.history_file, mode='a', header=False, index=False)
            logger.info(f"Updated partido with ID {partido_id}")
            return updated_partido_dict
        except NotFoundException:
            raise
        except Exception as e:
            logger.error(f"Error updating partido {partido_id}: {str(e)}")
            raise RuntimeError(f"Error al actualizar partido {partido_id}: {str(e)}") from e

    def delete(self, partido_id: str) -> None:
        try:
            if partido_id not in self.df["id"].values:
                raise NotFoundException("Partido", partido_id)
            partido = self.df[self.df["id"] == partido_id].to_dict(orient='records')[0]
            self.df = self.df[self.df["id"] != partido_id]
            self.df.to_csv(self.csv_file, index=False)
            history_df = pd.DataFrame([partido])
            history_df["action"] = "delete"
            history_df["timestamp"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            history_df.to_csv(self.history_file, mode='a', header=False, index=False)
            logger.info(f"Deleted partido with ID {partido_id}")
        except NotFoundException:
            raise
        except Exception as e:
            logger.error(f"Error deleting partido {partido_id}: {str(e)}")
            raise RuntimeError(f"Error al eliminar partido {partido_id}: {str(e)}") from e

class TorneoOps:
    def __init__(self, csv_file: str = "data/torneos.csv", history_file: str = "data/torneos_history.csv"):
        self.csv_file = csv_file
        self.history_file = history_file
        try:
            self.df = pd.read_csv(csv_file)
            expected_columns = ["id", "nombre", "fecha_inicio", "fecha_fin", "campeon"]
            for col in expected_columns:
                if col not in self.df.columns:
                    self.df[col] = None
            if not pd.io.common.file_exists(history_file):
                pd.DataFrame(columns=expected_columns + ["action", "timestamp"]).to_csv(history_file, index=False)
        except FileNotFoundError:
            logger.warning(f"File {csv_file} not found, creating empty DataFrame")
            self.df = pd.DataFrame(columns=["id", "nombre", "fecha_inicio", "fecha_fin", "campeon"])
            pd.DataFrame(columns=["id", "nombre", "fecha_inicio", "fecha_fin", "campeon", "action", "timestamp"]).to_csv(history_file, index=False)

    def get_all(self) -> List[dict]:
        return self.df.to_dict(orient='records')

    def get_by_id(self, torneo_id: int) -> dict:
        try:
            torneo = self.df[self.df["id"] == torneo_id].to_dict(orient='records')
            if not torneo:
                raise NotFoundException("Torneo", str(torneo_id))
            return torneo[0]
        except NotFoundException:
            raise
        except Exception as e:
            logger.error(f"Error in get_by_id for {torneo_id}: {str(e)}")
            raise RuntimeError(f"Error al obtener torneo {torneo_id}: {str(e)}") from e

    def create(self, torneo: Torneo) -> dict:
        try:
            if torneo.id in self.df["id"].values:
                raise DuplicateException("Torneo", str(torneo_id))
            torneo_dict = torneo.dict()
            new_df = pd.DataFrame([torneo_dict])
            self.df = pd.concat([self.df, new_df], ignore_index=True)
            self.df.to_csv(self.csv_file, index=False)
            history_df = pd.DataFrame([torneo_dict.copy()])
            history_df["action"] = "create"
            history_df["timestamp"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            history_df.to_csv(self.history_file, mode='a', header=False, index=False)
            logger.info(f"Created torneo with ID {torneo.id}")
            return torneo_dict
        except DuplicateException:
            raise
        except Exception as e:
            logger.error(f"Error creating torneo: {str(e)}")
            raise RuntimeError(f"Error al crear torneo: {str(e)}") from e

    def update(self, torneo_id: int, updated_torneo: Torneo) -> dict:
        try:
            if torneo_id not in self.df["id"].values:
                raise NotFoundException("Torneo", str(torneo_id))
            original = self.df[self.df["id"] == torneo_id].to_dict(orient='records')[0]
            updated_torneo_dict = updated_torneo.dict()
            updated_torneo_dict["id"] = torneo_id
            self.df.loc[self.df["id"] == torneo_id] = updated_torneo_dict
            self.df.to_csv(self.csv_file, index=False)
            history_df = pd.DataFrame([original])
            history_df["action"] = "update"
            history_df["timestamp"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            history_df.to_csv(self.history_file, mode='a', header=False, index=False)
            logger.info(f"Updated torneo with ID {torneo_id}")
            return updated_torneo_dict
        except NotFoundException:
            raise
        except Exception as e:
            logger.error(f"Error updating torneo {torneo_id}: {str(e)}")
            raise RuntimeError(f"Error al actualizar torneo {torneo_id}: {str(e)}") from e

    def delete(self, torneo_id: int) -> None:
        try:
            if torneo_id not in self.df["id"].values:
                raise NotFoundException("Torneo", str(torneo_id))
            torneo = self.df[self.df["id"] == torneo_id].to_dict(orient='records')[0]
            self.df = self.df[self.df["id"] != torneo_id]
            self.df.to_csv(self.csv_file, index=False)
            history_df = pd.DataFrame([torneo])
            history_df["action"] = "delete"
            history_df["timestamp"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            history_df.to_csv(self.history_file, mode='a', header=False, index=False)
            logger.info(f"Deleted torneo with ID {torneo_id}")
        except NotFoundException:
            raise
        except Exception as e:
            logger.error(f"Error deleting torneo {torneo_id}: {str(e)}")
            raise RuntimeError(f"Error al eliminar torneo {torneo_id}: {str(e)}") from e

class PlantillaOps:
    def __init__(self, csv_file: str = "data/plantilla.csv", history_file: str = "data/plantilla_history.csv"):
        self.csv_file = csv_file
        self.history_file = history_file
        try:
            self.df = pd.read_csv(csv_file)
            expected_columns = ["id", "torneo_id", "equipo_id", "jugador_id"]
            for col in expected_columns:
                if col not in self.df.columns:
                    self.df[col] = None
            if not pd.io.common.file_exists(history_file):
                pd.DataFrame(columns=expected_columns + ["action", "timestamp"]).to_csv(history_file, index=False)
        except FileNotFoundError:
            logger.warning(f"File {csv_file} not found, creating empty DataFrame")
            self.df = pd.DataFrame(columns=["id", "torneo_id", "equipo_id", "jugador_id"])
            pd.DataFrame(columns=["id", "torneo_id", "equipo_id", "jugador_id", "action", "timestamp"]).to_csv(history_file, index=False)

    def get_all(self) -> List[dict]:
        return self.df.to_dict(orient='records')

    def get_by_id(self, plantilla_id: int) -> dict:
        try:
            plantilla = self.df[self.df["id"] == plantilla_id].to_dict(orient='records')
            if not plantilla:
                raise NotFoundException("Plantilla", str(plantilla_id))
            return plantilla[0]
        except NotFoundException:
            raise
        except Exception as e:
            logger.error(f"Error in get_by_id for {plantilla_id}: {str(e)}")
            raise RuntimeError(f"Error al obtener plantilla {plantilla_id}: {str(e)}") from e

    def create(self, plantilla: Plantilla) -> dict:
        try:
            if plantilla.id in self.df["id"].values:
                raise DuplicateException("Plantilla", str(plantilla.id))
            plantilla_dict = plantilla.dict()
            new_df = pd.DataFrame([plantilla_dict])
            self.df = pd.concat([self.df, new_df], ignore_index=True)
            self.df.to_csv(self.csv_file, index=False)
            history_df = pd.DataFrame([plantilla_dict.copy()])
            history_df["action"] = "create"
            history_df["timestamp"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            history_df.to_csv(self.history_file, mode='a', header=False, index=False)
            logger.info(f"Created plantilla with ID {plantilla.id}")
            return plantilla_dict
        except DuplicateException:
            raise
        except Exception as e:
            logger.error(f"Error creating plantilla: {str(e)}")
            raise RuntimeError(f"Error al crear plantilla: {str(e)}") from e

    def update(self, plantilla_id: int, updated_plantilla: Plantilla) -> dict:
        try:
            if plantilla_id not in self.df["id"].values:
                raise NotFoundException("Plantilla", str(plantilla_id))
            original = self.df[self.df["id"] == plantilla_id].to_dict(orient='records')[0]
            updated_plantilla_dict = updated_plantilla.dict()
            updated_plantilla_dict["id"] = plantilla_id
            self.df.loc[self.df["id"] == plantilla_id] = updated_plantilla_dict
            self.df.to_csv(self.csv_file, index=False)
            history_df = pd.DataFrame([original])
            history_df["action"] = "update"
            history_df["timestamp"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            history_df.to_csv(self.history_file, mode='a', header=False, index=False)
            logger.info(f"Updated plantilla with ID {plantilla_id}")
            return updated_plantilla_dict
        except NotFoundException:
            raise
        except Exception as e:
            logger.error(f"Error updating plantilla {plantilla_id}: {str(e)}")
            raise RuntimeError(f"Error al actualizar plantilla {plantilla_id}: {str(e)}") from e

    def delete(self, plantilla_id: int) -> None:
        try:
            if plantilla_id not in self.df["id"].values:
                raise NotFoundException("Plantilla", str(plantilla_id))
            plantilla = self.df[self.df["id"] == plantilla_id].to_dict(orient='records')[0]
            self.df = self.df[self.df["id"] != plantilla_id]
            self.df.to_csv(self.csv_file, index=False)
            history_df = pd.DataFrame([plantilla])
            history_df["action"] = "delete"
            history_df["timestamp"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            history_df.to_csv(self.history_file, mode='a', header=False, index=False)
            logger.info(f"Deleted plantilla with ID {plantilla_id}")
        except NotFoundException:
            raise
        except Exception as e:
            logger.error(f"Error deleting plantilla {plantilla_id}: {str(e)}")
            raise RuntimeError(f"Error al eliminar plantilla {plantilla_id}: {str(e)}") from e

# Instancias de operaciones con DataFrames precargados
equipo_ops = EquipoOps("data/equipos.csv")
jugador_ops = JugadorOps("data/jugadores.csv")
partido_ops = PartidoOps("data/partidos.csv")
torneo_ops = TorneoOps()
plantilla_ops = PlantillaOps()

# Endpoints
@app.get("/", response_class=HTMLResponse)
async def read_index(request: Request):
    try:
        return templates.TemplateResponse("index.html", {"request": request})
    except Exception as e:
        logger.error(f"Error in read_index: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/equipos/", response_class=HTMLResponse)
async def get_equipos(request: Request):
    try:
        equipos = equipo_ops.get_all()
        return templates.TemplateResponse("equipos.html", {"request": request, "equipos": equipos})
    except Exception as e:
        logger.error(f"Error in get_equipos: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/equipos/{equipo_id}", response_class=HTMLResponse)
async def get_equipo(request: Request, equipo_id: str):
    try:
        equipo = equipo_ops.get_by_id(equipo_id)
        logger.info(f"Cargando detalles de equipo ID {equipo_id}: {equipo}")
        return templates.TemplateResponse("equipodetalle.html", {"request": request, "equipo": equipo})
    except NotFoundException as e:
        raise HTTPException(status_code=404, detail=str(e.detail))
    except Exception as e:
        logger.error(f"Error in get_equipo: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/equipos/")
async def create_equipo(request: Request, id: str = Form(...), nombre: str = Form(...), pais: str = Form(...), enfrentamientos_con_colombia: int = Form(...)):
    try:
        equipo = Equipo(id=id, nombre=nombre, pais=pais, enfrentamientos_con_colombia=enfrentamientos_con_colombia)
        equipo_ops.create(equipo)
        return RedirectResponse(url="/equipos/", status_code=303)
    except DuplicateException as e:
        raise HTTPException(status_code=400, detail=str(e.detail))
    except Exception as e:
        logger.error(f"Error in create_equipo: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

@app.put("/equipos/{equipo_id}")
async def update_equipo(equipo_id: str, request: Request, nombre: str = Form(None), pais: str = Form(None), enfrentamientos_con_colombia: int = Form(None)):
    try:
        updated_equipo = Equipo(id=equipo_id, nombre=nombre or "", pais=pais or "", enfrentamientos_con_colombia=enfrentamientos_con_colombia or 0)
        equipo_ops.update(equipo_id, updated_equipo)
        return RedirectResponse(url="/equipos/", status_code=303)
    except NotFoundException as e:
        raise HTTPException(status_code=404, detail=str(e.detail))
    except Exception as e:
        logger.error(f"Error in update_equipo: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/equipos/{equipo_id}")
async def delete_equipo(equipo_id: str):
    try:
        equipo_ops.delete(equipo_id)
        return RedirectResponse(url="/equipos/", status_code=303)
    except NotFoundException as e:
        raise HTTPException(status_code=404, detail=str(e.detail))
    except Exception as e:
        logger.error(f"Error in delete_equipo: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/jugadores/", response_class=HTMLResponse)
async def get_jugadores(request: Request, anio: int = None, page: int = 1):
    try:
        per_page = 10
        jugadores, total = jugador_ops.get_paginated(page, per_page, anio)
        total_pages = (total + per_page - 1) // per_page
        logger.info(f"Total jugadores: {total}, Páginas: {total_pages}")
        return templates.TemplateResponse(
            "jugadores.html",
            {
                "request": request,
                "jugadores": jugadores,
                "anio": anio,
                "page": page,
                "total_pages": total_pages
            }
        )
    except Exception as e:
        logger.error(f"Error in get_jugadores: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/jugadores/{jugador_id}", response_class=HTMLResponse)
async def get_jugador(request: Request, jugador_id: int):
    try:
        jugador = jugador_ops.get_by_id(jugador_id)
        logger.info(f"Cargando detalles de jugador ID {jugador_id}: {jugador}")
        return templates.TemplateResponse("jugadordetalle.html", {"request": request, "jugador": jugador})
    except NotFoundException as e:
        raise HTTPException(status_code=404, detail=str(e.detail))
    except Exception as e:
        logger.error(f"Error in get_jugador: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/jugadores/{jugador_id}/edit", response_class=HTMLResponse)
async def edit_jugador(request: Request, jugador_id: int):
    try:
        jugador = jugador_ops.get_by_id(jugador_id)
        return templates.TemplateResponse("jugadores_edit.html", {"request": request, "jugador": jugador})
    except NotFoundException as e:
        raise HTTPException(status_code=404, detail=str(e.detail))
    except Exception as e:
        logger.error(f"Error in edit_jugador: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/jugadores/")
async def create_jugador(
    request: Request,
    id: int = Form(...),
    Jugadores: str = Form(...),
    F_Nacim_Edad: str = Form(...),
    Club: str = Form(...),
    Altura: str = Form(None),
    Pie: str = Form(None),
    Partidos_con_la_seleccion: int = Form(None),
    Goles: int = Form(None),
    Numero_de_camisa: str = Form(None),
    anio: int = Form(...),
    posicion: str = Form(...),
    activo: bool = Form(...)
):
    try:
        jugador = Jugador(
            id=id,
            Jugadores=Jugadores,
            F_Nacim_Edad=F_Nacim_Edad,
            Club=Club,
            Altura=Altura,
            Pie=Pie,
            Partidos_con_la_seleccion=Partidos_con_la_seleccion,
            Goles=Goles,
            Numero_de_camisa=Numero_de_camisa,
            anio=anio,
            posicion=posicion,
            activo=activo
        )
        jugador_ops.create(jugador)
        return RedirectResponse(url="/jugadores/", status_code=303)
    except DuplicateException as e:
        raise HTTPException(status_code=400, detail=str(e.detail))
    except Exception as e:
        logger.error(f"Error in create_jugador: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/jugadores/{jugador_id}/")
async def handle_jugador_methods(
    request: Request,
    jugador_id: int,
    _method: str = Form(None),
    id: int = Form(None),
    Jugadores: str = Form(None),
    F_Nacim_Edad: str = Form(None),
    Club: str = Form(None),
    Altura: str = Form(None),
    Pie: str = Form(None),
    Partidos_con_la_seleccion: int = Form(None),
    Goles: int = Form(None),
    Numero_de_camisa: str = Form(None),
    anio: int = Form(None),
    posicion: str = Form(None),
    activo: bool = Form(None)
):
    try:
        if _method == "PUT":
            jugador = Jugador(
                id=jugador_id,
                Jugadores=Jugadores or "",
                F_Nacim_Edad=F_Nacim_Edad or "",
                Club=Club or "",
                Altura=Altura,
                Pie=Pie,
                Partidos_con_la_seleccion=Partidos_con_la_seleccion,
                Goles=Goles,
                Numero_de_camisa=Numero_de_camisa,
                anio=anio or 0,
                posicion=posicion or "",
                activo=activo if activo is not None else True
            )
            jugador_ops.update(jugador_id, jugador)
            return RedirectResponse(url="/jugadores/", status_code=303)
        elif _method == "DELETE":
            jugador_ops.delete(jugador_id)
            return RedirectResponse(url="/jugadores/", status_code=303)
        else:
            raise HTTPException(status_code=400, detail="Método no soportado")
    except NotFoundException as e:
        raise HTTPException(status_code=404, detail=str(e.detail))
    except Exception as e:
        logger.error(f"Error in handle_jugador_methods: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/partidos/", response_class=HTMLResponse)
async def get_partidos(request: Request):
    try:
        partidos = partido_ops.get_all()
        return templates.TemplateResponse("partidos.html", {"request": request, "partidos": partidos})
    except Exception as e:
        logger.error(f"Error in get_partidos: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/partidos/{partido_id}", response_class=HTMLResponse)
async def get_partido(request: Request, partido_id: str):
    try:
        partido = partido_ops.get_by_id(partido_id)
        return templates.TemplateResponse("partidodetalle.html", {"request": request, "partido": partido})
    except NotFoundException as e:
        raise HTTPException(status_code=404, detail=str(e.detail))
    except Exception as e:
        logger.error(f"Error in get_partido: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/partidos/{partido_id}/edit", response_class=HTMLResponse)
async def edit_partido(request: Request, partido_id: str):
    try:
        partido = partido_ops.get_by_id(partido_id)
        return templates.TemplateResponse("partidos_edit.html", {"request": request, "partido": partido})
    except NotFoundException as e:
        raise HTTPException(status_code=404, detail=str(e.detail))
    except Exception as e:
        logger.error(f"Error in edit_partido: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/partidos/")
async def create_partido(
    request: Request,
    id: str = Form(...),
    fecha: str = Form(...),
    equipo_local: str = Form(...),
    equipo_visitante: str = Form(...),
    goles_local: int = Form(...),
    goles_visitante: int = Form(...),
    torneo_id: int = Form(...),
    eliminado: str = Form(None),
    tarjetas_amarillas_local: int = Form(None),
    tarjetas_amarillas_visitante: int = Form(None),
    tarjetas_rojas_local: int = Form(None),
    tarjetas_rojas_visitante: int = Form(None)
):
    try:
        partido = Partido(
            id=id,
            fecha=fecha,
            equipo_local=equipo_local,
            equipo_visitante=equipo_visitante,
            goles_local=goles_local,
            goles_visitante=goles_visitante,
            torneo_id=torneo_id,
            eliminado=eliminado,
            tarjetas_amarillas_local=tarjetas_amarillas_local,
            tarjetas_amarillas_visitante=tarjetas_amarillas_visitante,
            tarjetas_rojas_local=tarjetas_rojas_local,
            tarjetas_rojas_visitante=tarjetas_rojas_visitante
        )
        partido_ops.create(partido)
        return RedirectResponse(url="/partidos/", status_code=303)
    except DuplicateException as e:
        raise HTTPException(status_code=400, detail=str(e.detail))
    except Exception as e:
        logger.error(f"Error in create_partido: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/partidos/{partido_id}/")
async def handle_partido_methods(
    request: Request,
    partido_id: str,
    _method: str = Form(None),
    id: str = Form(None),
    fecha: str = Form(None),
    equipo_local: str = Form(None),
    equipo_visitante: str = Form(None),
    goles_local: int = Form(None),
    goles_visitante: int = Form(None),
    torneo_id: int = Form(None),
    eliminado: str = Form(None),
    tarjetas_amarillas_local: int = Form(None),
    tarjetas_amarillas_visitante: int = Form(None),
    tarjetas_rojas_local: int = Form(None),
    tarjetas_rojas_visitante: int = Form(None)
):
    try:
        if _method == "PUT":
            partido = Partido(
                id=partido_id,
                fecha=fecha,
                equipo_local=equipo_local,
                equipo_visitante=equipo_visitante,
                goles_local=goles_local,
                goles_visitante=goles_visitante,
                torneo_id=torneo_id,
                eliminado=eliminado,
                tarjetas_amarillas_local=tarjetas_amarillas_local,
                tarjetas_amarillas_visitante=tarjetas_amarillas_visitante,
                tarjetas_rojas_local=tarjetas_rojas_local,
                tarjetas_rojas_visitante=tarjetas_rojas_visitante
            )
            partido_ops.update(partido_id, partido)
            return RedirectResponse(url="/partidos/", status_code=303)
        elif _method == "DELETE":
            partido_ops.delete(partido_id)
            return RedirectResponse(url="/partidos/", status_code=303)
        else:
            raise HTTPException(status_code=400, detail="Método no soportado")
    except NotFoundException as e:
        raise HTTPException(status_code=404, detail=str(e.detail))
    except Exception as e:
        logger.error(f"Error in handle_partido_methods: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/torneos/", response_class=HTMLResponse)
async def get_torneos(request: Request):
    try:
        torneos = torneo_ops.get_all()
        return templates.TemplateResponse("torneos.html", {"request": request, "torneos": torneos})
    except Exception as e:
        logger.error(f"Error in get_torneos: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/torneos/{torneo_id}", response_class=HTMLResponse)
async def get_torneo(request: Request, torneo_id: int):
    try:
        torneo = torneo_ops.get_by_id(torneo_id)
        return templates.TemplateResponse("torneodetalle.html", {"request": request, "torneo": torneo})
    except NotFoundException as e:
        raise HTTPException(status_code=404, detail=str(e.detail))
    except Exception as e:
        logger.error(f"Error in get_torneo: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/torneos/{torneo_id}/edit", response_class=HTMLResponse)
async def edit_torneo(request: Request, torneo_id: int):
    try:
        torneo = torneo_ops.get_by_id(torneo_id)
        return templates.TemplateResponse("torneos_edit.html", {"request": request, "torneo": torneo})
    except NotFoundException as e:
        raise HTTPException(status_code=404, detail=str(e.detail))
    except Exception as e:
        logger.error(f"Error in edit_torneo: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/torneos/")
async def create_torneo(
    request: Request,
    id: int = Form(...),
    nombre: str = Form(...),
    fecha_inicio: str = Form(...),
    fecha_fin: str = Form(...),
    campeon: str = Form(None)
):
    try:
        torneo = Torneo(
            id=id,
            nombre=nombre,
            fecha_inicio=fecha_inicio,
            fecha_fin=fecha_fin,
            campeon=campeon
        )
        torneo_ops.create(torneo)
        return RedirectResponse(url="/torneos/", status_code=303)
    except DuplicateException as e:
        raise HTTPException(status_code=400, detail=str(e.detail))
    except Exception as e:
        logger.error(f"Error in create_torneo: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/torneos/{torneo_id}/")
async def handle_torneo_methods(
    request: Request,
    torneo_id: int,
    _method: str = Form(None),
    id: int = Form(None),
    nombre: str = Form(None),
    fecha_inicio: str = Form(None),
    fecha_fin: str = Form(None),
    campeon: str = Form(None)
):
    try:
        if _method == "PUT":
            torneo = Torneo(
                id=torneo_id,
                nombre=nombre,
                fecha_inicio=fecha_inicio,
                fecha_fin=fecha_fin,
                campeon=campeon
            )
            torneo_ops.update(torneo_id, torneo)
            return RedirectResponse(url="/torneos/", status_code=303)
        elif _method == "DELETE":
            torneo_ops.delete(torneo_id)
            return RedirectResponse(url="/torneos/", status_code=303)
        else:
            raise HTTPException(status_code=400, detail="Método no soportado")
    except NotFoundException as e:
        raise HTTPException(status_code=404, detail=str(e.detail))
    except Exception as e:
        logger.error(f"Error in handle_torneo_methods: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/plantillas/", response_class=HTMLResponse)
async def get_plantillas(request: Request):
    try:
        plantillas = plantilla_ops.get_all()
        return templates.TemplateResponse("plantillas.html", {"request": request, "plantillas": plantillas})
    except Exception as e:
        logger.error(f"Error in get_plantillas: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/plantillas/{plantilla_id}", response_class=HTMLResponse)
async def get_plantilla(request: Request, plantilla_id: int):
    try:
        plantilla = plantilla_ops.get_by_id(plantilla_id)
        return templates.TemplateResponse("plantilladetalle.html", {"request": request, "plantilla": plantilla})
    except NotFoundException as e:
        raise HTTPException(status_code=404, detail=str(e.detail))
    except Exception as e:
        logger.error(f"Error in get_plantilla: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/plantillas/{plantilla_id}/edit", response_class=HTMLResponse)
async def edit_plantilla(request: Request, plantilla_id: int):
    try:
        plantilla = plantilla_ops.get_by_id(plantilla_id)
        return templates.TemplateResponse("plantillas_edit.html", {"request": request, "plantilla": plantilla})
    except NotFoundException as e:
        raise HTTPException(status_code=404, detail=str(e.detail))
    except Exception as e:
        logger.error(f"Error in edit_plantilla: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/plantillas/")
async def create_plantilla(
    request: Request,
    id: int = Form(...),
    torneo_id: int = Form(...),
    equipo_id: str = Form(...),
    jugador_id: int = Form(...)
):
    try:
        plantilla = Plantilla(
            id=id,
            torneo_id=torneo_id,
            equipo_id=equipo_id,
            jugador_id=jugador_id
        )
        plantilla_ops.create(plantilla)
        return RedirectResponse(url="/plantillas/", status_code=303)
    except DuplicateException as e:
        raise HTTPException(status_code=400, detail=str(e.detail))
    except Exception as e:
        logger.error(f"Error in create_plantilla: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/plantillas/{plantilla_id}/")
async def handle_plantilla_methods(
    request: Request,
    plantilla_id: int,
    _method: str = Form(None),
    id: int = Form(None),
    torneo_id: int = Form(None),
    equipo_id: str = Form(None),
    jugador_id: int = Form(None)
):
    try:
        if _method == "PUT":
            plantilla = Plantilla(
                id=plantilla_id,
                torneo_id=torneo_id,
                equipo_id=equipo_id,
                jugador_id=jugador_id
            )
            plantilla_ops.update(plantilla_id, plantilla)
            return RedirectResponse(url="/plantillas/", status_code=303)
        elif _method == "DELETE":
            plantilla_ops.delete(plantilla_id)
            return RedirectResponse(url="/plantillas/", status_code=303)
        else:
            raise HTTPException(status_code=400, detail="Método no soportado")
    except NotFoundException as e:
        raise HTTPException(status_code=404, detail=str(e.detail))
    except Exception as e:
        logger.error(f"Error in handle_plantilla_methods: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/estadisticas/completa/", response_class=HTMLResponse)
async def get_full_stats(request: Request, anio: int = None):
    try:
        if anio:
            validate_year(anio)
            partidos = partido_ops.get_by_year(anio)
        else:
            partidos = partido_ops.get_all()
        if not partidos:
            return templates.TemplateResponse(
                "estadisticas.html",
                {"request": request, "estadisticas": {"message": f"No se encontraron partidos para el año {anio}"}}
            )
        total_partidos = len(partidos)
        goles_anotados = sum(p.get("goles_local", 0) for p in partidos if p.get("equipo_local", "").lower() == "colombia") + \
                         sum(p.get("goles_visitante", 0) for p in partidos if p.get("equipo_visitante", "").lower() == "colombia")
        goles_recibidos = sum(p.get("goles_visitante", 0) for p in partidos if p.get("equipo_local", "").lower() == "colombia") + \
                          sum(p.get("goles_local", 0) for p in partidos if p.get("equipo_visitante", "").lower() == "colombia")
        victorias = sum(1 for p in partidos if (p.get("equipo_local", "").lower() == "colombia" and p.get("goles_local", 0) > p.get("goles_visitante", 0)) or
                        (p.get("equipo_visitante", "").lower() == "colombia" and p.get("goles_visitante", 0) > p.get("goles_local", 0)))
        empates = sum(1 for p in partidos if ((p.get("equipo_local", "").lower() == "colombia" or p.get("equipo_visitante", "").lower() == "colombia") and
                                              p.get("goles_local", 0) == p.get("goles_visitante", 0)))
        derrotas = total_partidos - victorias - empates
        promedio_goles = round(goles_anotados / total_partidos, 2) if total_partidos > 0 else 0
        tarjetas_amarillas = sum(p.get("tarjetas_amarillas_local", 0) for p in partidos if p.get("equipo_local", "").lower() == "colombia") + \
                             sum(p.get("tarjetas_amarillas_visitante", 0) for p in partidos if p.get("equipo_visitante", "").lower() == "colombia")
        tarjetas_rojas = sum(p.get("tarjetas_rojas_local", 0) for p in partidos if p.get("equipo_local", "").lower() == "colombia") + \
                         sum(p.get("tarjetas_rojas_visitante", 0) for p in partidos if p.get("equipo_visitante", "").lower() == "colombia")
        partidos_eliminados = sum(1 for p in partidos if p.get("eliminado", "").lower() == "colombia" and
                                  (p.get("equipo_local", "").lower() == "colombia" or p.get("equipo_visitante", "").lower() == "colombia"))
        porcentaje_eliminaciones = round((partidos_eliminados / total_partidos) * 100, 2) if total_partidos > 0 else 0

        # Preparar datos para gráficas
        resultados_data = {
            "labels": ["Victorias", "Empates", "Derrotas"],
            "datasets": [{
                "label": "Resultados",
                "data": [victorias, empates, derrotas],
                "backgroundColor": ["#28a745", "#ffc107", "#dc3545"]
            }]
        }

        fechas = [p["fecha"] for p in partidos]
        goles_anotados_lista = [
            p["goles_local"] if p["equipo_local"].lower() == "colombia" else p["goles_visitante"]
            for p in partidos
        ]
        goles_recibidos_lista = [
            p["goles_visitante"] if p["equipo_local"].lower() == "colombia" else p["goles_local"]
            for p in partidos
        ]
        goles_data = {
            "labels": fechas,
            "datasets": [
                {
                    "label": "Goles Anotados",
                    "data": goles_anotados_lista,
                    "borderColor": "#28a745",
                    "fill": False
                },
                {
                    "label": "Goles Recibidos",
                    "data": goles_recibidos_lista,
                    "borderColor": "#dc3545",
                    "fill": False
                }
            ]
        }

        estadisticas = {
            "total_partidos": total_partidos,
            "goles_anotados": goles_anotados,
            "goles_recibidos": goles_recibidos,
            "promedio_goles_por_partido": promedio_goles,
            "victorias": victorias,
            "empates": empates,
            "derrotas": derrotas,
            "tarjetas_amarillas": tarjetas_amarillas,
            "tarjetas_rojas": tarjetas_rojas,
            "partidos_eliminados": partidos_eliminados,
            "porcentaje_eliminaciones": porcentaje_eliminaciones,
            "resultados_data": resultados_data,
            "goles_data": goles_data
        }
        return templates.TemplateResponse("estadisticas.html", {"request": request, "estadisticas": estadisticas})
    except Exception as e:
        logger.error(f"Error in get_full_stats: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error al calcular estadísticas: {str(e)}")
