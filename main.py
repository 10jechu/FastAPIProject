from typing import List, Dict
from fastapi import FastAPI, HTTPException, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from datetime import datetime
import logging
import pandas as pd
from pydantic import BaseModel
from models.equipo import Equipo
from models.jugador import Jugador
from models.partido import Partido
from models.plantilla import Plantilla
from models.torneo import Torneo
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
    if year not in range(2021, 2026):
        raise HTTPException(status_code=400, detail="El año debe estar entre 2021 y 2025")

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

# Clases de Operaciones
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
            if not pd.io.common.file_exists(history_file):
                pd.DataFrame(columns=["id", "nombre", "pais", "enfrentamientos_con_colombia", "action", "timestamp"]).to_csv(history_file, index=False)
        except FileNotFoundError:
            logger.warning(f"File {csv_file} not found, creating empty DataFrame")
            self.df = pd.DataFrame(columns=["id", "nombre", "pais", "enfrentamientos_con_colombia"])
            pd.DataFrame(columns=["id", "nombre", "pais", "enfrentamientos_con_colombia", "action", "timestamp"]).to_csv(history_file, index=False)

    def get_all(self) -> List[dict]:
        return self.df.to_dict(orient='records')

    def get_by_id(self, equipo_id: str) -> dict:
        try:
            equipo = self.df[self.df["id"] == equipo_id].to_dict(orient='records')
            if not equipo:
                raise NotFoundException("Equipo", equipo_id)
            return equipo[0]
        except NotFoundException:
            raise
        except Exception as e:
            logger.error(f"Error in get_by_id for {equipo_id}: {str(e)}")
            raise

    def create(self, equipo: Equipo) -> dict:
        try:
            if str(equipo.id) in self.df["id"].values:
                raise DuplicateException("Equipo", str(equipo.id))
            equipo_dict = equipo.dict()
            new_df = pd.DataFrame([equipo_dict])
            self.df = pd.concat([self.df, new_df], ignore_index=True)
            self.df.to_csv(self.csv_file, index=False)
            history_df = pd.DataFrame([{"id": equipo.id, "nombre": equipo.nombre, "pais": equipo.pais, "enfrentamientos_con_colombia": equipo.enfrentamientos_con_colombia, "action": "create", "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")}])
            history_df.to_csv(self.history_file, mode='a', header=False, index=False)
            return equipo_dict
        except DuplicateException:
            raise
        except Exception as e:
            logger.error(f"Error creating equipo: {str(e)}")
            raise

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
            return updated_equipo_dict
        except NotFoundException:
            raise
        except Exception as e:
            logger.error(f"Error updating equipo {equipo_id}: {str(e)}")
            raise

    def delete(self, equipo_id: str) -> None:
        try:
            if equipo_id not in self.df["id"].values:
                raise NotFoundException("Equipo", equipo_id)
            equipo = self.df[self.df["id"] == equipo_id].to_dict(orient='records')[0]
            self.df = self.df[self.df["id"] != equipo_id]
            self.df.to_csv(self.csv_file, index=False)
            history_df = pd.DataFrame([{"id": equipo_id, "nombre": equipo["nombre"], "pais": equipo["pais"], "enfrentamientos_con_colombia": equipo["enfrentamientos_con_colombia"], "action": "delete", "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")}])
            history_df.to_csv(self.history_file, mode='a', header=False, index=False)
        except NotFoundException:
            raise
        except Exception as e:
            logger.error(f"Error deleting equipo {equipo_id}: {str(e)}")
            raise

class JugadorOps:
    def __init__(self, csv_file: str, history_file: str = "data/jugadores_history.csv", trash_file: str = "data/jugadores_trash.csv"):
        self.csv_file = csv_file
        self.history_file = history_file
        self.trash_file = trash_file
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
            if not pd.io.common.file_exists(history_file):
                pd.DataFrame(columns=["id", "Jugadores", "F_Nacim_Edad", "Club", "Altura", "Pie", "Partidos_con_la_seleccion", "Goles", "Numero_de_camisa", "anio", "posicion", "activo", "action", "timestamp"]).to_csv(history_file, index=False)
            if not pd.io.common.file_exists(trash_file):
                pd.DataFrame(columns=["id", "Jugadores", "F_Nacim_Edad", "Club", "Altura", "Pie", "Partidos_con_la_seleccion", "Goles", "Numero_de_camisa", "anio", "posicion", "activo", "deleted_timestamp"]).to_csv(trash_file, index=False)
        except FileNotFoundError:
            logger.warning(f"File {csv_file} not found, creating empty DataFrame")
            self.df = pd.DataFrame(columns=["id", "Jugadores", "F_Nacim_Edad", "Club", "Altura", "Pie", "Partidos_con_la_seleccion", "Goles", "Numero_de_camisa", "anio", "posicion", "activo"])
            pd.DataFrame(columns=["id", "Jugadores", "F_Nacim_Edad", "Club", "Altura", "Pie", "Partidos_con_la_seleccion", "Goles", "Numero_de_camisa", "anio", "posicion", "activo", "action", "timestamp"]).to_csv(history_file, index=False)
            pd.DataFrame(columns=["id", "Jugadores", "F_Nacim_Edad", "Club", "Altura", "Pie", "Partidos_con_la_seleccion", "Goles", "Numero_de_camisa", "anio", "posicion", "activo", "deleted_timestamp"]).to_csv(trash_file, index=False)

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
            return jugador
        except NotFoundException:
            raise
        except Exception as e:
            logger.error(f"Error in get_by_id for {jugador_id}: {str(e)}")
            raise

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
            return jugador_dict
        except DuplicateException:
            raise
        except Exception as e:
            logger.error(f"Error creating jugador: {str(e)}")
            raise

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
            return updated_jugador_dict
        except NotFoundException:
            raise
        except Exception as e:
            logger.error(f"Error updating jugador {jugador_id}: {str(e)}")
            raise

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
            trash_df = pd.DataFrame([jugador])
            trash_df["deleted_timestamp"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            trash_df.to_csv(self.trash_file, mode='a', header=False, index=False)
        except NotFoundException:
            raise
        except Exception as e:
            logger.error(f"Error deleting jugador {jugador_id}: {str(e)}")
            raise

    def get_trash(self) -> List[dict]:
        try:
            if pd.io.common.file_exists(self.trash_file):
                trash_df = pd.read_csv(self.trash_file)
                return trash_df.to_dict(orient='records')
            return []
        except Exception as e:
            logger.error(f"Error getting trash: {str(e)}")
            return []

class PartidoOps:
    def __init__(self, csv_file: str, history_file: str = "data/partidos_history.csv"):
        self.csv_file = csv_file
        self.history_file = history_file
        try:
            self.df = pd.read_csv(csv_file)
            self.df['fecha'] = pd.to_datetime(self.df['fecha'], errors='coerce')
            expected_columns = ["id", "equipo_local", "equipo_visitante", "fecha", "goles_local", "goles_visitante", "torneo_id", "eliminado", "tarjetas_amarillas_local", "tarjetas_amarillas_visitante", "tarjetas_rojas_local", "tarjetas_rojas_visitante"]
            for col in expected_columns:
                if col not in self.df.columns:
                    self.df[col] = None
            self.df['id'] = self.df['id'].astype(str)
            self.df['torneo_id'] = self.df['torneo_id'].astype(str)
            if not pd.io.common.file_exists(history_file):
                pd.DataFrame(columns=expected_columns + ["action", "timestamp"]).to_csv(history_file, index=False)
        except FileNotFoundError:
            logger.warning(f"File {csv_file} not found, creating empty DataFrame")
            self.df = pd.DataFrame(columns=["id", "equipo_local", "equipo_visitante", "fecha", "goles_local", "goles_visitante", "torneo_id", "eliminado", "tarjetas_amarillas_local", "tarjetas_amarillas_visitante", "tarjetas_rojas_local", "tarjetas_rojas_visitante"])
            pd.DataFrame(columns=["id", "equipo_local", "equipo_visitante", "fecha", "goles_local", "goles_visitante", "torneo_id", "eliminado", "tarjetas_amarillas_local", "tarjetas_amarillas_visitante", "tarjetas_rojas_local", "tarjetas_rojas_visitante", "action", "timestamp"]).to_csv(history_file, index=False)

    def get_all(self) -> List[dict]:
        return self.df.to_dict(orient='records')

    def get_by_id(self, partido_id: str) -> dict:
        try:
            partido = self.df[self.df["id"].astype(str) == str(partido_id)].to_dict(orient='records')
            if not partido:
                raise NotFoundException("Partido", partido_id)
            return partido[0]
        except NotFoundException:
            raise
        except Exception as e:
            logger.error(f"Error in get_by_id for {partido_id}: {str(e)}")
            raise

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
            if str(partido.id) in self.df["id"].astype(str).values:
                raise DuplicateException("Partido", str(partido.id))
            partido_dict = partido.dict()
            new_df = pd.DataFrame([partido_dict])
            self.df = pd.concat([self.df, new_df], ignore_index=True)
            self.df.to_csv(self.csv_file, index=False)
            history_df = pd.DataFrame([partido_dict.copy()])
            history_df["action"] = "create"
            history_df["timestamp"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            history_df.to_csv(self.history_file, mode='a', header=False, index=False)
            return partido_dict
        except DuplicateException:
            raise
        except Exception as e:
            logger.error(f"Error creating partido: {str(e)}")
            raise

    def update(self, partido_id: str, updated_partido: Partido) -> dict:
        try:
            if partido_id not in self.df["id"].astype(str).values:
                raise NotFoundException("Partido", partido_id)
            original = self.df[self.df["id"].astype(str) == partido_id].to_dict(orient='records')[0]
            updated_partido_dict = updated_partido.dict()
            updated_partido_dict["id"] = partido_id
            self.df.loc[self.df["id"].astype(str) == partido_id] = updated_partido_dict
            self.df.to_csv(self.csv_file, index=False)
            history_df = pd.DataFrame([original])
            history_df["action"] = "update"
            history_df["timestamp"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            history_df.to_csv(self.history_file, mode='a', header=False, index=False)
            return updated_partido_dict
        except NotFoundException:
            raise
        except Exception as e:
            logger.error(f"Error updating partido {partido_id}: {str(e)}")
            raise

    def delete(self, partido_id: str) -> None:
        try:
            if partido_id not in self.df["id"].astype(str).values:
                raise NotFoundException("Partido", partido_id)
            partido = self.df[self.df["id"].astype(str) == partido_id].to_dict(orient='records')[0]
            self.df = self.df[self.df["id"].astype(str) != partido_id]
            self.df.to_csv(self.csv_file, index=False)
            history_df = pd.DataFrame([partido])
            history_df["action"] = "delete"
            history_df["timestamp"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            history_df.to_csv(self.history_file, mode='a', header=False, index=False)
        except NotFoundException:
            raise
        except Exception as e:
            logger.error(f"Error deleting partido {partido_id}: {str(e)}")
            raise

class TorneoOps:
    def __init__(self, csv_file: str, history_file: str = "data/torneos_history.csv"):
        self.csv_file = csv_file
        self.history_file = history_file
        try:
            self.df = pd.read_csv(csv_file)
            expected_columns = ["id", "nombre", "anio", "pais_anfitrion", "estado", "eliminado"]
            for col in expected_columns:
                if col not in self.df.columns:
                    self.df[col] = None
            self.df['id'] = self.df['id'].astype(str)
            if not pd.io.common.file_exists(history_file):
                pd.DataFrame(columns=["id", "nombre", "anio", "pais_anfitrion", "estado", "eliminado", "action", "timestamp"]).to_csv(history_file, index=False)
        except FileNotFoundError:
            logger.warning(f"File {csv_file} not found, creating empty DataFrame")
            self.df = pd.DataFrame(columns=["id", "nombre", "anio", "pais_anfitrion", "estado", "eliminado"])
            pd.DataFrame(columns=["id", "nombre", "anio", "pais_anfitrion", "estado", "eliminado", "action", "timestamp"]).to_csv(history_file, index=False)

    def get_all(self) -> List[dict]:
        return self.df.to_dict(orient='records')

    def get_by_id(self, torneo_id: str) -> dict:
        try:
            torneo = self.df[self.df["id"] == torneo_id].to_dict(orient='records')
            if not torneo:
                raise NotFoundException("Torneo", torneo_id)
            return torneo[0]
        except NotFoundException:
            raise
        except Exception as e:
            logger.error(f"Error in get_by_id for {torneo_id}: {str(e)}")
            raise

    def create(self, torneo: Torneo) -> dict:
        try:
            if str(torneo.id) in self.df["id"].values:
                raise DuplicateException("Torneo", str(torneo.id))
            torneo_dict = torneo.dict()
            new_df = pd.DataFrame([torneo_dict])
            self.df = pd.concat([self.df, new_df], ignore_index=True)
            self.df.to_csv(self.csv_file, index=False)
            history_df = pd.DataFrame([torneo_dict.copy()])
            history_df["action"] = "create"
            history_df["timestamp"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            history_df.to_csv(self.history_file, mode='a', header=False, index=False)
            return torneo_dict
        except DuplicateException:
            raise
        except Exception as e:
            logger.error(f"Error creating torneo: {str(e)}")
            raise

    def update(self, torneo_id: str, updated_torneo: Torneo) -> dict:
        try:
            if torneo_id not in self.df["id"].values:
                raise NotFoundException("Torneo", torneo_id)
            original = self.df[self.df["id"] == torneo_id].to_dict(orient='records')[0]
            updated_torneo_dict = updated_torneo.dict()
            updated_torneo_dict["id"] = torneo_id
            self.df.loc[self.df["id"] == torneo_id] = updated_torneo_dict
            self.df.to_csv(self.csv_file, index=False)
            history_df = pd.DataFrame([original])
            history_df["action"] = "update"
            history_df["timestamp"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            history_df.to_csv(self.history_file, mode='a', header=False, index=False)
            return updated_torneo_dict
        except NotFoundException:
            raise
        except Exception as e:
            logger.error(f"Error updating torneo {torneo_id}: {str(e)}")
            raise

    def delete(self, torneo_id: str) -> None:
        try:
            if torneo_id not in self.df["id"].values:
                raise NotFoundException("Torneo", torneo_id)
            torneo = self.df[self.df["id"] == torneo_id].to_dict(orient='records')[0]
            self.df = self.df[self.df["id"] != torneo_id]
            self.df.to_csv(self.csv_file, index=False)
            history_df = pd.DataFrame([torneo])
            history_df["action"] = "delete"
            history_df["timestamp"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            history_df.to_csv(self.history_file, mode='a', header=False, index=False)
        except NotFoundException:
            raise
        except Exception as e:
            logger.error(f"Error deleting torneo {torneo_id}: {str(e)}")
            raise

class PlantillaOps:
    def __init__(self, csv_file: str, history_file: str = "data/plantillas_history.csv"):
        self.csv_file = csv_file
        self.history_file = history_file
        try:
            self.df = pd.read_csv(csv_file)
            expected_columns = ["id", "equipo_id", "nombre", "posicion", "anio"]
            for col in expected_columns:
                if col not in self.df.columns:
                    self.df[col] = None
            self.df['id'] = self.df['id'].astype(str)
            if not pd.io.common.file_exists(history_file):
                pd.DataFrame(columns=["id", "equipo_id", "nombre", "posicion", "anio", "action", "timestamp"]).to_csv(history_file, index=False)
        except FileNotFoundError:
            logger.warning(f"File {csv_file} not found, creating empty DataFrame")
            self.df = pd.DataFrame(columns=["id", "equipo_id", "nombre", "posicion", "anio"])
            pd.DataFrame(columns=["id", "equipo_id", "nombre", "posicion", "anio", "action", "timestamp"]).to_csv(history_file, index=False)

    def get_all(self) -> List[dict]:
        return self.df.to_dict(orient='records')

    def get_by_id(self, plantilla_id: str) -> dict:
        try:
            plantilla = self.df[self.df["id"] == plantilla_id].to_dict(orient='records')
            if not plantilla:
                raise NotFoundException("Plantilla", str(plantilla_id))
            return plantilla[0]
        except NotFoundException:
            raise
        except Exception as e:
            logger.error(f"Error in get_by_id for {plantilla_id}: {str(e)}")
            raise

    def create(self, plantilla: Plantilla) -> dict:
        try:
            if str(plantilla.id) in self.df["id"].astype(str).values:
                raise DuplicateException("Plantilla", str(plantilla.id))
            plantilla_dict = plantilla.dict()
            new_df = pd.DataFrame([plantilla_dict])
            self.df = pd.concat([self.df, new_df], ignore_index=True)
            self.df.to_csv(self.csv_file, index=False)
            history_df = pd.DataFrame([plantilla_dict.copy()])
            history_df["action"] = "create"
            history_df["timestamp"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            history_df.to_csv(self.history_file, mode='a', header=False, index=False)
            return plantilla_dict
        except DuplicateException:
            raise
        except Exception as e:
            logger.error(f"Error creating plantilla: {str(e)}")
            raise

    def update(self, plantilla_id: str, updated_plantilla: Plantilla) -> dict:
        try:
            if plantilla_id not in self.df["id"].astype(str).values:
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
            return updated_plantilla_dict
        except NotFoundException:
            raise
        except Exception as e:
            logger.error(f"Error updating plantilla {plantilla_id}: {str(e)}")
            raise

    def delete(self, plantilla_id: str) -> None:
        try:
            if plantilla_id not in self.df["id"].astype(str).values:
                raise NotFoundException("Plantilla", str(plantilla_id))
            plantilla = self.df[self.df["id"] == plantilla_id].to_dict(orient='records')[0]
            self.df = self.df[self.df["id"] != plantilla_id]
            self.df.to_csv(self.csv_file, index=False)
            history_df = pd.DataFrame([plantilla])
            history_df["action"] = "delete"
            history_df["timestamp"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            history_df.to_csv(self.history_file, mode='a', header=False, index=False)
        except NotFoundException:
            raise
        except Exception as e:
            logger.error(f"Error deleting plantilla {plantilla_id}: {str(e)}")
            raise

# Instancias de operaciones
equipo_ops = EquipoOps("data/equipos.csv")
jugador_ops = JugadorOps("data/jugadores.csv")
partido_ops = PartidoOps("data/partidos.csv")
torneo_ops = TorneoOps("data/torneos.csv")
plantilla_ops = PlantillaOps("data/plantilla.csv")

# Rutas
@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
    jugadores = jugador_ops.get_all()[:5]  # Mostrar solo 5 jugadores en el inicio
    equipos = equipo_ops.get_all()[:5]
    partidos = partido_ops.get_all()[:5]
    torneos = torneo_ops.get_all()[:5]
    plantillas = plantilla_ops.get_all()[:5]
    return templates.TemplateResponse("index.html", {
        "request": request,
        "jugadores": jugadores,
        "equipos": equipos,
        "partidos": partidos,
        "torneos": torneos,
        "plantillas": plantillas
    })

# Equipos
@app.get("/equipos/", response_class=HTMLResponse)
async def get_equipos(request: Request):
    try:
        equipos = equipo_ops.get_all()
        return templates.TemplateResponse("equipos.html", {"request": request, "equipos": equipos})
    except Exception as e:
        logger.error(f"Error in get_equipos: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/equipos/crear", response_class=HTMLResponse)
async def create_equipo_form(request: Request):
    return templates.TemplateResponse("equipos_crear.html", {"request": request})

@app.get("/equipos/{equipo_id}", response_class=HTMLResponse)
async def get_equipo(request: Request, equipo_id: str):
    try:
        equipo = equipo_ops.get_by_id(equipo_id)
        return templates.TemplateResponse("equipo_detail.html", {"request": request, "equipo": equipo})
    except NotFoundException as e:
        raise HTTPException(status_code=404, detail=str(e.detail))
    except Exception as e:
        logger.error(f"Error in get_equipo: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/equipos/{equipo_id}/edit", response_class=HTMLResponse)
async def edit_equipo_form(request: Request, equipo_id: str):
    try:
        equipo = equipo_ops.get_by_id(equipo_id)
        return templates.TemplateResponse("equipos_edit.html", {"request": request, "equipo": equipo})
    except NotFoundException as e:
        raise HTTPException(status_code=404, detail=str(e.detail))
    except Exception as e:
        logger.error(f"Error in edit_equipo_form: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/equipos/")
async def create_equipo(
    request: Request,
    id: str = Form(...),
    nombre: str = Form(...),
    pais: str = Form(...),
    enfrentamientos_con_colombia: int = Form(...)
):
    try:
        equipo = Equipo(id=id, nombre=nombre, pais=pais, enfrentamientos_con_colombia=enfrentamientos_con_colombia)
        equipo_ops.create(equipo)
        return RedirectResponse(url="/equipos/", status_code=303)
    except DuplicateException as e:
        raise HTTPException(status_code=400, detail=str(e.detail))
    except Exception as e:
        logger.error(f"Error in create_equipo: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/equipos/{equipo_id}/")
async def handle_equipo_methods(
    request: Request,
    equipo_id: str,
    method: str = Form(None),
    id: str = Form(None),
    nombre: str = Form(None),
    pais: str = Form(None),
    enfrentamientos_con_colombia: int = Form(None)
):
    try:
        if method == "PUT":
            equipo = Equipo(
                id=equipo_id,
                nombre=nombre or "",
                pais=pais or "",
                enfrentamientos_con_colombia=enfrentamientos_con_colombia or 0
            )
            equipo_ops.update(equipo_id, equipo)
            return RedirectResponse(url="/equipos/", status_code=303)
        elif method == "DELETE":
            equipo_ops.delete(equipo_id)
            return RedirectResponse(url="/equipos/", status_code=303)
        else:
            raise HTTPException(status_code=400, detail="Método no soportado")
    except NotFoundException as e:
        raise HTTPException(status_code=404, detail=str(e.detail))
    except Exception as e:
        logger.error(f"Error in handle_equipo_methods: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# Jugadores
@app.get("/jugadores/", response_class=HTMLResponse)
async def get_jugadores(request: Request, page: int = 1, anio: int = None):
    try:
        per_page = 10
        jugadores, total = jugador_ops.get_paginated(page, per_page, anio)
        total_pages = (total + per_page - 1) // per_page
        trash = jugador_ops.get_trash()
        return templates.TemplateResponse(
            "jugadores.html",
            {"request": request, "jugadores": jugadores, "page": page, "total_pages": total_pages, "anio": anio, "trash": trash}
        )
    except HTTPException as e:
        raise
    except Exception as e:
        logger.error(f"Error in get_jugadores: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/jugadores/crear", response_class=HTMLResponse)
async def create_jugador_form(request: Request):
    return templates.TemplateResponse("jugadores_crear.html", {"request": request})

@app.get("/jugadores/{jugador_id}", response_class=HTMLResponse)
async def get_jugador(request: Request, jugador_id: int):
    try:
        jugador = jugador_ops.get_by_id(jugador_id)
        return templates.TemplateResponse("jugador_detail.html", {"request": request, "jugador": jugador})
    except NotFoundException as e:
        raise HTTPException(status_code=404, detail=str(e.detail))
    except Exception as e:
        logger.error(f"Error in get_jugador: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/jugadores/{jugador_id}/edit", response_class=HTMLResponse)
async def edit_jugador_form(request: Request, jugador_id: int):
    try:
        jugador = jugador_ops.get_by_id(jugador_id)
        return templates.TemplateResponse("jugadores_edit.html", {"request": request, "jugador": jugador})
    except NotFoundException as e:
        raise HTTPException(status_code=404, detail=str(e.detail))
    except Exception as e:
        logger.error(f"Error in edit_jugador_form: {str(e)}")
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
    Numero_de_camisa: int = Form(None),
    anio: int = Form(...),
    posicion: str = Form(None),
    activo: bool = Form(True)
):
    try:
        jugador = Jugador(
            id=id,
            Jugadores=Jugadores,
            F_Nacim_Edad=F_Nacim_Edad,
            Club=Club,
            Altura=Altura,
            Pie=Pie,
            Partidos_con_la_seleccion=Partidos_con_la_seleccion or 0,
            Goles=Goles or 0,
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
        logger.error(f"Error in create_jugador: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/jugadores/{jugador_id}/")
async def handle_jugador_methods(
    request: Request,
    jugador_id: int,
    method: str = Form(None),
    id: int = Form(None),
    Jugadores: str = Form(None),
    F_Nacim_Edad: str = Form(None),
    Club: str = Form(None),
    Altura: str = Form(None),
    Pie: str = Form(None),
    Partidos_con_la_seleccion: int = Form(None),
    Goles: int = Form(None),
    Numero_de_camisa: int = Form(None),
    anio: int = Form(None),
    posicion: str = Form(None),
    activo: bool = Form(None)
):
    try:
        if method == "PUT":
            jugador = Jugador(
                id=jugador_id,
                Jugadores=Jugadores or "",
                F_Nacim_Edad=F_Nacim_Edad or "",
                Club=Club or "",
                Altura=Altura if Altura else None,
                Pie=Pie if Pie else None,
                Partidos_con_la_seleccion=Partidos_con_la_seleccion if Partidos_con_la_seleccion is not None else 0,
                Goles=Goles if Goles is not None else 0,
                Numero_de_camisa=Numero_de_camisa if Numero_de_camisa is not None else 0,
                anio=anio or 0,
                posicion=posicion or "",
                activo=activo if activo is not None else True
            )
            jugador_ops.update(jugador_id, jugador)
            return RedirectResponse(url="/jugadores/", status_code=303)
        elif method == "DELETE":
            jugador_ops.delete(jugador_id)
            return RedirectResponse(url="/jugadores/", status_code=303)
        else:
            raise HTTPException(status_code=400, detail="Método no soportado")
    except NotFoundException as e:
        raise HTTPException(status_code=404, detail=str(e.detail))
    except Exception as e:
        logger.error(f"Error in handle_jugador_methods: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# Partidos
@app.get("/partidos/", response_class=HTMLResponse)
async def get_partidos(request: Request):
    try:
        partidos = partido_ops.get_all()
        return templates.TemplateResponse("partidos.html", {"request": request, "partidos": partidos})
    except Exception as e:
        logger.error(f"Error in get_partidos: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/partidos/crear", response_class=HTMLResponse)
async def create_partido_form(request: Request):
    return templates.TemplateResponse("partidos_crear.html", {"request": request})

@app.get("/partidos/{partido_id}", response_class=HTMLResponse)
async def get_partido(request: Request, partido_id: str):
    try:
        partido = partido_ops.get_by_id(partido_id)
        return templates.TemplateResponse("partido_detail.html", {"request": request, "partido": partido})
    except NotFoundException as e:
        raise HTTPException(status_code=404, detail=str(e.detail))
    except Exception as e:
        logger.error(f"Error in get_partido: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/partidos/{partido_id}/edit", response_class=HTMLResponse)
async def edit_partido_form(request: Request, partido_id: str):
    try:
        partido = partido_ops.get_by_id(partido_id)
        return templates.TemplateResponse("partidos_edit.html", {"request": request, "partido": partido})
    except NotFoundException as e:
        raise HTTPException(status_code=404, detail=str(e.detail))
    except Exception as e:
        logger.error(f"Error in edit_partido_form: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/partidos/")
async def create_partido(
    request: Request,
    id: str = Form(...),
    equipo_local: str = Form(...),
    equipo_visitante: str = Form(...),
    fecha: str = Form(...),
    goles_local: int = Form(...),
    goles_visitante: int = Form(...),
    torneo_id: str = Form(...),
    eliminado: str = Form(None),
    tarjetas_amarillas_local: int = Form(None),
    tarjetas_amarillas_visitante: int = Form(None),
    tarjetas_rojas_local: int = Form(None),
    tarjetas_rojas_visitante: int = Form(None)
):
    try:
        from datetime import datetime
        fecha_date = datetime.strptime(fecha, "%Y-%m-%d").date()
        partido = Partido(
            id=id,
            equipo_local=equipo_local,
            equipo_visitante=equipo_visitante,
            fecha=fecha_date,
            goles_local=goles_local,
            goles_visitante=goles_visitante,
            torneo_id=torneo_id,
            eliminado=eliminado,
            tarjetas_amarillas_local=tarjetas_amarillas_local or 0,
            tarjetas_amarillas_visitante=tarjetas_amarillas_visitante or 0,
            tarjetas_rojas_local=tarjetas_rojas_local or 0,
            tarjetas_rojas_visitante=tarjetas_rojas_visitante or 0
        )
        partido_ops.create(partido)
        return RedirectResponse(url="/partidos/", status_code=303)
    except DuplicateException as e:
        raise HTTPException(status_code=400, detail=str(e.detail))
    except Exception as e:
        logger.error(f"Error in create_partido: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/partidos/{partido_id}/")
async def handle_partido_methods(
    request: Request,
    partido_id: str,
    method: str = Form(None),
    id: str = Form(None),
    equipo_local: str = Form(None),
    equipo_visitante: str = Form(None),
    fecha: str = Form(None),
    goles_local: int = Form(None),
    goles_visitante: int = Form(None),
    torneo_id: str = Form(None),
    eliminado: str = Form(None),
    tarjetas_amarillas_local: int = Form(None),
    tarjetas_amarillas_visitante: int = Form(None),
    tarjetas_rojas_local: int = Form(None),
    tarjetas_rojas_visitante: int = Form(None)
):
    try:
        if method == "PUT":
            from datetime import datetime
            fecha_date = datetime.strptime(fecha, "%Y-%m-%d").date() if fecha else None
            partido = Partido(
                id=partido_id,
                equipo_local=equipo_local or "",
                equipo_visitante=equipo_visitante or "",
                fecha=fecha_date,
                goles_local=goles_local or 0,
                goles_visitante=goles_visitante or 0,
                torneo_id=torneo_id or "",
                eliminado=eliminado,
                tarjetas_amarillas_local=tarjetas_amarillas_local or 0,
                tarjetas_amarillas_visitante=tarjetas_amarillas_visitante or 0,
                tarjetas_rojas_local=tarjetas_rojas_local or 0,
                tarjetas_rojas_visitante=tarjetas_rojas_visitante or 0
            )
            partido_ops.update(partido_id, partido)
            return RedirectResponse(url="/partidos/", status_code=303)
        elif method == "DELETE":
            partido_ops.delete(partido_id)
            return RedirectResponse(url="/partidos/", status_code=303)
        else:
            raise HTTPException(status_code=400, detail="Método no soportado")
    except NotFoundException as e:
        raise HTTPException(status_code=404, detail=str(e.detail))
    except Exception as e:
        logger.error(f"Error in handle_partido_methods: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# Torneos
@app.get("/torneos/", response_class=HTMLResponse)
async def get_torneos(request: Request):
    try:
        torneos = torneo_ops.get_all()
        return templates.TemplateResponse("torneos.html", {"request": request, "torneos": torneos})
    except Exception as e:
        logger.error(f"Error in get_torneos: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/torneos/crear", response_class=HTMLResponse)
async def create_torneo_form(request: Request):
    return templates.TemplateResponse("torneos_crear.html", {"request": request})

@app.get("/torneos/{torneo_id}", response_class=HTMLResponse)
async def get_torneo(request: Request, torneo_id: str):
    try:
        torneo = torneo_ops.get_by_id(torneo_id)
        return templates.TemplateResponse("torneo_detail.html", {"request": request, "torneo": torneo})
    except NotFoundException as e:
        raise HTTPException(status_code=404, detail=str(e.detail))
    except Exception as e:
        logger.error(f"Error in get_torneo: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/torneos/{torneo_id}/edit", response_class=HTMLResponse)
async def edit_torneo_form(request: Request, torneo_id: str):
    try:
        torneo = torneo_ops.get_by_id(torneo_id)
        return templates.TemplateResponse("torneos_edit.html", {"request": request, "torneo": torneo})
    except NotFoundException as e:
        raise HTTPException(status_code=404, detail=str(e.detail))
    except Exception as e:
        logger.error(f"Error in edit_torneo_form: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/torneos/")
async def create_torneo(
    request: Request,
    id: str = Form(...),
    nombre: str = Form(...),
    anio: int = Form(...),
    pais_anfitrion: str = Form(None),
    estado: str = Form(...),
    eliminado: str = Form(None)
):
    try:
        torneo = Torneo(id=id, nombre=nombre, anio=anio, pais_anfitrion=pais_anfitrion, estado=estado, eliminado=eliminado)
        torneo_ops.create(torneo)
        return RedirectResponse(url="/torneos/", status_code=303)
    except DuplicateException as e:
        raise HTTPException(status_code=400, detail=str(e.detail))
    except Exception as e:
        logger.error(f"Error in create_torneo: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/torneos/{torneo_id}/")
async def handle_torneo_methods(
    request: Request,
    torneo_id: str,
    method: str = Form(None),
    id: str = Form(None),
    nombre: str = Form(None),
    anio: int = Form(None),
    pais_anfitrion: str = Form(None),
    estado: str = Form(None),
    eliminado: str = Form(None)
):
    try:
        if method == "PUT":
            torneo = Torneo(
                id=torneo_id,
                nombre=nombre or "",
                anio=anio or 0,
                pais_anfitrion=pais_anfitrion,
                estado=estado or "",
                eliminado=eliminado
            )
            torneo_ops.update(torneo_id, torneo)
            return RedirectResponse(url="/torneos/", status_code=303)
        elif method == "DELETE":
            torneo_ops.delete(torneo_id)
            return RedirectResponse(url="/torneos/", status_code=303)
        else:
            raise HTTPException(status_code=400, detail="Método no soportado")
    except NotFoundException as e:
        raise HTTPException(status_code=404, detail=str(e.detail))
    except Exception as e:
        logger.error(f"Error in handle_torneo_methods: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# Plantillas
@app.get("/plantillas/", response_class=HTMLResponse)
async def get_plantillas(request: Request):
    try:
        plantillas = plantilla_ops.get_all()
        return templates.TemplateResponse("plantillas.html", {"request": request, "plantillas": plantillas})
    except Exception as e:
        logger.error(f"Error in get_plantillas: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/plantillas/crear", response_class=HTMLResponse)
async def create_plantilla_form(request: Request):
    return templates.TemplateResponse("plantillas_crear.html", {"request": request})

@app.get("/plantillas/{plantilla_id}", response_class=HTMLResponse)
async def get_plantilla(request: Request, plantilla_id: str):
    try:
        plantilla = plantilla_ops.get_by_id(plantilla_id)
        return templates.TemplateResponse("plantilla_detail.html", {"request": request, "plantilla": plantilla})
    except NotFoundException as e:
        raise HTTPException(status_code=404, detail=str(e.detail))
    except Exception as e:
        logger.error(f"Error in get_plantilla: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/plantillas/{plantilla_id}/edit", response_class=HTMLResponse)
async def edit_plantilla_form(request: Request, plantilla_id: str):
    try:
        plantilla = plantilla_ops.get_by_id(plantilla_id)
        return templates.TemplateResponse("plantillas_edit.html", {"request": request, "plantilla": plantilla})
    except NotFoundException as e:
        raise HTTPException(status_code=404, detail=str(e.detail))
    except Exception as e:
        logger.error(f"Error in edit_plantilla_form: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/plantillas/")
async def create_plantilla(
    request: Request,
    id: str = Form(...),
    equipo_id: str = Form(...),
    nombre: str = Form(None),
    posicion: str = Form(None),
    anio: int = Form(...)
):
    try:
        plantilla = Plantilla(id=id, equipo_id=equipo_id, nombre=nombre, posicion=posicion, anio=anio)
        plantilla_ops.create(plantilla)
        return RedirectResponse(url="/plantillas/", status_code=303)
    except DuplicateException as e:
        raise HTTPException(status_code=400, detail=str(e.detail))
    except Exception as e:
        logger.error(f"Error in create_plantilla: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/plantillas/{plantilla_id}/")
async def handle_plantilla_methods(
    request: Request,
    plantilla_id: str,
    method: str = Form(None),
    id: str = Form(None),
    equipo_id: str = Form(None),
    nombre: str = Form(None),
    posicion: str = Form(None),
    anio: int = Form(None)
):
    try:
        if method == "PUT":
            plantilla = Plantilla(
                id=plantilla_id,
                equipo_id=equipo_id or "",
                nombre=nombre,
                posicion=posicion,
                anio=anio or 0
            )
            plantilla_ops.update(plantilla_id, plantilla)
            return RedirectResponse(url="/plantillas/", status_code=303)
        elif method == "DELETE":
            plantilla_ops.delete(plantilla_id)
            return RedirectResponse(url="/plantillas/", status_code=303)
        else:
            raise HTTPException(status_code=400, detail="Método no soportado")
    except NotFoundException as e:
        raise HTTPException(status_code=404, detail=str(e.detail))
    except Exception as e:
        logger.error(f"Error in handle_plantilla_methods: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# Estadísticas
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
            "porcentaje_eliminaciones": porcentaje_eliminaciones
        }
        return templates.TemplateResponse("estadisticas.html", {"request": request, "estadisticas": estadisticas})
    except Exception as e:
        logger.error(f"Error in get_full_stats: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error al calcular estadísticas: {str(e)}")

# Documentación
@app.get("/documentacion/", response_class=HTMLResponse)
async def get_documentacion(request: Request):
    return templates.TemplateResponse("documentacion.html", {"request": request})