from fastapi import FastAPI, Request, Form, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import pandas as pd
from pydantic import BaseModel
from typing import Optional
import os
import uuid
from datetime import datetime

app = FastAPI()

# Montar archivos estáticos (CSS, JS)
app.mount("/static", StaticFiles(directory="static"), name="static")

# Configurar Jinja2 para las plantillas
templates = Jinja2Templates(directory="templates")

# Directorios de datos
DATA_DIR = "data"
os.makedirs(DATA_DIR, exist_ok=True)

# Archivos CSV
JUGADORES_CSV = os.path.join(DATA_DIR, "jugadores.csv")
EQUIPOS_CSV = os.path.join(DATA_DIR, "equipos.csv")
PARTIDOS_CSV = os.path.join(DATA_DIR, "partidos.csv")
TORNEOS_CSV = os.path.join(DATA_DIR, "torneos.csv")
PLANTILLAS_CSV = os.path.join(DATA_DIR, "plantillas.csv")

# Inicializar archivos CSV si no existen
def init_csv(file_path, columns):
    if not os.path.exists(file_path):
        pd.DataFrame(columns=columns).to_csv(file_path, index=False)

init_csv(JUGADORES_CSV, ["id", "Jugadores", "F_Nacim_Edad", "Club", "Altura", "Pie", "Partidos_con_la_seleccion", "Goles", "Numero_de_camisa", "anio", "posicion", "activo"])
init_csv(EQUIPOS_CSV, ["id", "nombre", "pais", "enfrentamientos_con_colombia"])
init_csv(PARTIDOS_CSV, ["id", "equipo_local", "equipo_visitante", "fecha", "goles_local", "goles_visitante", "torneo_id", "eliminado", "tarjetas_amarillas_local", "tarjetas_amarillas_visitante", "tarjetas_rojas_local", "tarjetas_rojas_visitante"])
init_csv(TORNEOS_CSV, ["id", "nombre", "anio", "pais_anfitrion", "estado", "eliminado"])
init_csv(PLANTILLAS_CSV, ["id", "equipo_id", "nombre", "posicion", "anio"])

# Modelos Pydantic
class Jugador(BaseModel):
    id: Optional[str] = None
    Jugadores: str
    F_Nacim_Edad: str
    Club: Optional[str] = None
    Altura: Optional[str] = None
    Pie: Optional[str] = None
    Partidos_con_la_seleccion: Optional[int] = 0
    Goles: Optional[int] = 0
    Numero_de_camisa: Optional[int] = None
    anio: int
    posicion: Optional[str] = None
    activo: bool = True

class Equipo(BaseModel):
    id: Optional[str] = None
    nombre: str
    pais: str
    enfrentamientos_con_colombia: int = 0

class Partido(BaseModel):
    id: Optional[str] = None
    equipo_local: str
    equipo_visitante: str
    fecha: str
    goles_local: int
    goles_visitante: int
    torneo_id: Optional[str] = None
    eliminado: Optional[str] = None
    tarjetas_amarillas_local: int = 0
    tarjetas_amarillas_visitante: int = 0
    tarjetas_rojas_local: int = 0
    tarjetas_rojas_visitante: int = 0

class Torneo(BaseModel):
    id: Optional[str] = None
    nombre: str
    anio: int
    pais_anfitrion: Optional[str] = None
    estado: str
    eliminado: Optional[str] = None

class Plantilla(BaseModel):
    id: Optional[str] = None
    equipo_id: str
    nombre: Optional[str] = None
    posicion: Optional[str] = None
    anio: int

# Rutas CRUD para Jugadores
@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
    jugadores = pd.read_csv(JUGADORES_CSV).to_dict("records")
    equipos = pd.read_csv(EQUIPOS_CSV).to_dict("records")
    partidos = pd.read_csv(PARTIDOS_CSV).to_dict("records")
    torneos = pd.read_csv(TORNEOS_CSV).to_dict("records")
    plantillas = pd.read_csv(PLANTILLAS_CSV).to_dict("records")
    return templates.TemplateResponse(
        "index.html",
        {"request": request, "jugadores": jugadores[:5], "equipos": equipos[:5], "partidos": partidos[:5], "torneos": torneos[:5], "plantillas": plantillas[:5]}
    )

@app.get("/jugadores/", response_class=HTMLResponse)
async def get_jugadores(request: Request):
    jugadores = pd.read_csv(JUGADORES_CSV).to_dict("records")
    return templates.TemplateResponse("jugadores.html", {"request": request, "jugadores": jugadores})

@app.get("/jugadores/crear/", response_class=HTMLResponse)
async def create_jugador_form(request: Request):
    return templates.TemplateResponse("jugadores_crear.html", {"request": request})

@app.post("/jugadores/")
async def create_jugador(
    Jugadores: str = Form(...),
    F_Nacim_Edad: str = Form(...),
    Club: Optional[str] = Form(None),
    Altura: Optional[str] = Form(None),
    Pie: Optional[str] = Form(None),
    Partidos_con_la_seleccion: Optional[int] = Form(0),
    Goles: Optional[int] = Form(0),
    Numero_de_camisa: Optional[int] = Form(None),
    anio: int = Form(...),
    posicion: Optional[str] = Form(None),
    activo: bool = Form(True)
):
    df = pd.read_csv(JUGADORES_CSV)
    new_id = str(uuid.uuid4())
    new_jugador = {
        "id": new_id,
        "Jugadores": Jugadores,
        "F_Nacim_Edad": F_Nacim_Edad,
        "Club": Club,
        "Altura": Altura,
        "Pie": Pie,
        "Partidos_con_la_seleccion": Partidos_con_la_seleccion,
        "Goles": Goles,
        "Numero_de_camisa": Numero_de_camisa,
        "anio": anio,
        "posicion": posicion,
        "activo": activo
    }
    df = pd.concat([df, pd.DataFrame([new_jugador])], ignore_index=True)
    df.to_csv(JUGADORES_CSV, index=False)
    return {"message": "Jugador creado", "id": new_id}

@app.get("/jugadores/{id}", response_class=HTMLResponse)
async def get_jugador(request: Request, id: str):
    df = pd.read_csv(JUGADORES_CSV)
    jugador = df[df["id"] == id].to_dict("records")
    if not jugador:
        raise HTTPException(status_code=404, detail="Jugador no encontrado")
    return templates.TemplateResponse("jugador_detail.html", {"request": request, "jugador": jugador[0]})

@app.get("/jugadores/{id}/edit", response_class=HTMLResponse)
async def edit_jugador_form(request: Request, id: str):
    df = pd.read_csv(JUGADORES_CSV)
    jugador = df[df["id"] == id].to_dict("records")
    if not jugador:
        raise HTTPException(status_code=404, detail="Jugador no encontrado")
    return templates.TemplateResponse("jugadores_edit.html", {"request": request, "jugador": jugador[0]})

@app.post("/jugadores/{id}/")
async def update_jugador(
    id: str,
    Jugadores: str = Form(...),
    F_Nacim_Edad: str = Form(...),
    Club: Optional[str] = Form(None),
    Altura: Optional[str] = Form(None),
    Pie: Optional[str] = Form(None),
    Partidos_con_la_seleccion: Optional[int] = Form(0),
    Goles: Optional[int] = Form(0),
    Numero_de_camisa: Optional[int] = Form(None),
    anio: int = Form(...),
    posicion: Optional[str] = Form(None),
    activo: bool = Form(True),
    method: Optional[str] = Form(None)
):
    df = pd.read_csv(JUGADORES_CSV)
    if method == "DELETE":
        if id not in df["id"].values:
            raise HTTPException(status_code=404, detail="Jugador no encontrado")
        df = df[df["id"] != id]
        df.to_csv(JUGADORES_CSV, index=False)
        return {"message": "Jugador eliminado"}
    else:
        if id not in df["id"].values:
            raise HTTPException(status_code=404, detail="Jugador no encontrado")
        df.loc[df["id"] == id, ["Jugadores", "F_Nacim_Edad", "Club", "Altura", "Pie", "Partidos_con_la_seleccion", "Goles", "Numero_de_camisa", "anio", "posicion", "activo"]] = [
            Jugadores, F_Nacim_Edad, Club, Altura, Pie, Partidos_con_la_seleccion, Goles, Numero_de_camisa, anio, posicion, activo
        ]
        df.to_csv(JUGADORES_CSV, index=False)
        return {"message": "Jugador actualizado"}

# Rutas CRUD para Equipos
@app.get("/equipos/", response_class=HTMLResponse)
async def get_equipos(request: Request):
    equipos = pd.read_csv(EQUIPOS_CSV).to_dict("records")
    return templates.TemplateResponse("equipos.html", {"request": request, "equipos": equipos})

@app.get("/equipos/crear/", response_class=HTMLResponse)
async def create_equipo_form(request: Request):
    return templates.TemplateResponse("equipos_crear.html", {"request": request})

@app.post("/equipos/")
async def create_equipo(
    nombre: str = Form(...),
    pais: str = Form(...),
    enfrentamientos_con_colombia: int = Form(0)
):
    df = pd.read_csv(EQUIPOS_CSV)
    new_id = str(uuid.uuid4())
    new_equipo = {
        "id": new_id,
        "nombre": nombre,
        "pais": pais,
        "enfrentamientos_con_colombia": enfrentamientos_con_colombia
    }
    df = pd.concat([df, pd.DataFrame([new_equipo])], ignore_index=True)
    df.to_csv(EQUIPOS_CSV, index=False)
    return {"message": "Equipo creado", "id": new_id}

@app.get("/equipos/{id}", response_class=HTMLResponse)
async def get_equipo(request: Request, id: str):
    df = pd.read_csv(EQUIPOS_CSV)
    equipo = df[df["id"] == id].to_dict("records")
    if not equipo:
        raise HTTPException(status_code=404, detail="Equipo no encontrado")
    return templates.TemplateResponse("equipo_detail.html", {"request": request, "equipo": equipo[0]})

@app.get("/equipos/{id}/edit", response_class=HTMLResponse)
async def edit_equipo_form(request: Request, id: str):
    df = pd.read_csv(EQUIPOS_CSV)
    equipo = df[df["id"] == id].to_dict("records")
    if not equipo:
        raise HTTPException(status_code=404, detail="Equipo no encontrado")
    return templates.TemplateResponse("equipos_edit.html", {"request": request, "equipo": equipo[0]})

@app.post("/equipos/{id}/")
async def update_equipo(
    id: str,
    nombre: str = Form(...),
    pais: str = Form(...),
    enfrentamientos_con_colombia: int = Form(0),
    method: Optional[str] = Form(None)
):
    df = pd.read_csv(EQUIPOS_CSV)
    if method == "DELETE":
        if id not in df["id"].values:
            raise HTTPException(status_code=404, detail="Equipo no encontrado")
        df = df[df["id"] != id]
        df.to_csv(EQUIPOS_CSV, index=False)
        return {"message": "Equipo eliminado"}
    else:
        if id not in df["id"].values:
            raise HTTPException(status_code=404, detail="Equipo no encontrado")
        df.loc[df["id"] == id, ["nombre", "pais", "enfrentamientos_con_colombia"]] = [nombre, pais, enfrentamientos_con_colombia]
        df.to_csv(EQUIPOS_CSV, index=False)
        return {"message": "Equipo actualizado"}

# Rutas para Estadísticas
@app.get("/estadisticas/completa/", response_class=HTMLResponse)
async def get_estadisticas(request: Request, anio: Optional[int] = None):
    return templates.TemplateResponse("estadisticas.html", {"request": request})

@app.get("/estadisticas/completa/json")
async def get_estadisticas_json(anio: Optional[int] = None):
    df = pd.read_csv(PARTIDOS_CSV)
    if anio:
        df = df[pd.to_datetime(df["fecha"]).dt.year == anio]
    if df.empty:
        return {"total_partidos": 0, "message": "No se encontraron datos para este año."}
    total_partidos = len(df)
    goles_anotados = df[df["equipo_local"] == "Colombia"]["goles_local"].sum() + df[df["equipo_visitante"] == "Colombia"]["goles_visitante"].sum()
    goles_recibidos = df[df["equipo_local"] == "Colombia"]["goles_visitante"].sum() + df[df["equipo_visitante"] == "Colombia"]["goles_local"].sum()
    promedio_goles = (goles_anotados + goles_recibidos) / total_partidos if total_partidos > 0 else 0
    victorias = len(df[((df["equipo_local"] == "Colombia") & (df["goles_local"] > df["goles_visitante"])) | ((df["equipo_visitante"] == "Colombia") & (df["goles_visitante"] > df["goles_local"]))])
    empates = len(df[df["goles_local"] == df["goles_visitante"]])
    derrotas = total_partidos - victorias - empates
    return {
        "total_partidos": total_partidos,
        "goles_anotados": goles_anotados,
        "goles_recibidos": goles_recibidos,
        "promedio_goles_por_partido": round(promedio_goles, 2),
        "victorias": victorias,
        "empates": empates,
        "derrotas": derrotas,
        "tarjetas_amarillas": int(df["tarjetas_amarillas_local"].sum() + df["tarjetas_amarillas_visitante"].sum()),
        "tarjetas_rojas": int(df["tarjetas_rojas_local"].sum() + df["tarjetas_rojas_visitante"].sum()),
        "partidos_eliminados": len(df[df["eliminado"].notna()]),
        "porcentaje_eliminaciones": round((len(df[df["eliminado"].notna()]) / total_partidos * 100), 2) if total_partidos > 0 else 0
    }

# Rutas para Documentación
@app.get("/documentacion/", response_class=HTMLResponse)
async def get_documentacion(request: Request):
    return templates.TemplateResponse("documentacion.html", {"request": request})