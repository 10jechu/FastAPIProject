from fastapi import FastAPI, Request, HTTPException, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
import pandas as pd
from pydantic import BaseModel
from typing import List, Optional
import os
from datetime import datetime

app = FastAPI()
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

# Rutas de los archivos CSV
DATA_DIR = "data"
EQUIPOS_CSV = os.path.join(DATA_DIR, "equipos.csv")
JUGADORES_CSV = os.path.join(DATA_DIR, "jugadores.csv")
PARTIDOS_CSV = os.path.join(DATA_DIR, "partidos.csv")
PLANTILLA_CSV = os.path.join(DATA_DIR, "plantilla.csv")
TORNEOS_CSV = os.path.join(DATA_DIR, "torneos.csv")
HISTORY_DIR = os.path.join(DATA_DIR, "history")
TRASH_DIR = os.path.join(DATA_DIR, "trash")

# Crear directorios si no existen
os.makedirs(HISTORY_DIR, exist_ok=True)
os.makedirs(TRASH_DIR, exist_ok=True)

# Importar modelos
from models.equipo import Equipo
from models.jugador import Jugador
from models.partido import Partido
from models.plantilla import Plantilla
from models.torneo import Torneo

# Función para cargar CSV con manejo de nulos
def load_csv(file_path):
    try:
        if os.path.exists(file_path):
            df = pd.read_csv(file_path)
            # Reemplazar NaN con None para Pydantic
            df = df.where(pd.notnull(df), None)
            return df.to_dict('records')
        return []
    except pd.errors.EmptyDataError:
        return []
    except Exception as e:
        print(f"Error loading {file_path}: {e}")
        return []

# Funciones de carga por modelo
def load_equipos():
    return [Equipo(**item) for item in load_csv(EQUIPOS_CSV)]

def load_jugadores():
    return [Jugador(**item) for item in load_csv(JUGADORES_CSV)]

def load_partidos():
    return [Partido(**item) for item in load_csv(PARTIDOS_CSV)]

def load_plantillas():
    return [Plantilla(**item) for item in load_csv(PLANTILLA_CSV)]

def load_torneos():
    return [Torneo(**item) for item in load_csv(TORNEOS_CSV)]

# Funciones para guardar CSV
def save_csv(data, file_path):
    df = pd.DataFrame(data)
    df.to_csv(file_path, index=False)

# Funciones CRUD
def update_csv(data_list, file_path, new_data):
    data_dicts = [d.dict(exclude_unset=True) for d in data_list]
    new_data_dict = new_data.dict(exclude_unset=True)
    data_dicts = [d for d in data_dicts if str(d.get('id')) != str(new_data_dict.get('id'))]
    data_dicts.append(new_data_dict)
    save_csv(data_dicts, file_path)
    return [Equipo(**d) if 'nombre' in d else Jugador(**d) if 'Jugadores' in d else Partido(**d) if 'equipo_local' in d else Plantilla(**d) if 'equipo_id' in d else Torneo(**d) for d in data_dicts]

def delete_from_csv(data_list, file_path, id_to_delete):
    data_dicts = [d.dict(exclude_unset=True) for d in data_list]
    data_to_delete = next((d for d in data_dicts if str(d.get('id')) == str(id_to_delete)), None)
    if data_to_delete:
        data_dicts = [d for d in data_dicts if str(d.get('id')) != str(id_to_delete)]
        save_csv(data_dicts, file_path)
        history_file = file_path.replace(DATA_DIR, HISTORY_DIR).replace('.csv', f'_history_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv')
        trash_file = file_path.replace(DATA_DIR, TRASH_DIR).replace('.csv', '_trash.csv')
        os.makedirs(os.path.dirname(history_file), exist_ok=True)
        os.makedirs(os.path.dirname(trash_file), exist_ok=True)
        pd.DataFrame([data_to_delete]).to_csv(history_file, index=False)
        with open(trash_file, 'a') as f:
            pd.DataFrame([data_to_delete]).to_csv(f, index=False, header=not os.path.exists(trash_file))
    return [Equipo(**d) if 'nombre' in d else Jugador(**d) if 'Jugadores' in d else Partido(**d) if 'equipo_local' in d else Plantilla(**d) if 'equipo_id' in d else Torneo(**d) for d in data_dicts]

# Rutas principales
@app.get("/", response_class=HTMLResponse)
async def get_inicio(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.get("/equipos/", response_class=HTMLResponse)
async def get_equipos(request: Request):
    equipos = load_equipos()
    return templates.TemplateResponse("equipos.html", {"request": request, "equipos": equipos})

@app.get("/jugadores/", response_class=HTMLResponse)
async def get_jugadores(request: Request):
    jugadores = load_jugadores()
    return templates.TemplateResponse("jugadores.html", {"request": request, "jugadores": jugadores})

@app.get("/partidos/", response_class=HTMLResponse)
async def get_partidos(request: Request):
    partidos = load_partidos()
    torneos = load_torneos()  # Añadimos torneos para el filtrado
    return templates.TemplateResponse("partidos.html", {"request": request, "partidos": partidos, "torneos": torneos})

@app.get("/plantillas/", response_class=HTMLResponse)
async def get_plantillas(request: Request):
    plantillas = load_plantillas()
    return templates.TemplateResponse("plantillas.html", {"request": request, "plantillas": plantillas})

@app.get("/torneos/", response_class=HTMLResponse)
async def get_torneos(request: Request):
    torneos = load_torneos()
    return templates.TemplateResponse("torneos.html", {"request": request, "torneos": torneos})

@app.get("/estadisticas/completa/", response_class=HTMLResponse)
async def get_estadisticas(request: Request):
    partidos = load_partidos()
    stats = {
        "total_partidos": len(partidos),
        "goles_a_favor": sum(p.goles_local for p in partidos if p.equipo_local == "Colombia"),
        "goles_en_contra": sum(p.goles_visitante for p in partidos if p.equipo_local == "Colombia"),
        "victorias": len([p for p in partidos if p.equipo_local == "Colombia" and p.goles_local > p.goles_visitante]),
    }
    return templates.TemplateResponse("estadisticas.html", {"request": request, "stats": stats})

@app.get("/documentacion/", response_class=HTMLResponse)
async def get_documentacion(request: Request):
    return templates.TemplateResponse("documentacion.html", {"request": request})

# Rutas para detalles
@app.get("/equipos/{id}", response_class=HTMLResponse)
async def get_equipo(request: Request, id: int):
    equipos = load_equipos()
    equipo = next((e for e in equipos if e.id == id), None)
    if not equipo:
        raise HTTPException(status_code=404, detail="Equipo no encontrado")
    return templates.TemplateResponse("equipo_detail.html", {"request": request, "equipo": equipo})

@app.get("/jugadores/{id}", response_class=HTMLResponse)
async def get_jugador(request: Request, id: int):
    jugadores = load_jugadores()
    jugador = next((j for j in jugadores if j.id == id), None)
    if not jugador:
        raise HTTPException(status_code=404, detail="Jugador no encontrado")
    return templates.TemplateResponse("jugador_detail.html", {"request": request, "jugador": jugador})

@app.get("/partidos/{id}", response_class=HTMLResponse)
async def get_partido(request: Request, id: int):
    partidos = load_partidos()
    partido = next((p for p in partidos if p.id == id), None)
    if not partido:
        raise HTTPException(status_code=404, detail="Partido no encontrado")
    return templates.TemplateResponse("partido_detail.html", {"request": request, "partido": partido})

@app.get("/plantillas/{id}", response_class=HTMLResponse)
async def get_plantilla(request: Request, id: int):
    plantillas = load_plantillas()
    plantilla = next((p for p in plantillas if p.id == id), None)
    if not plantilla:
        raise HTTPException(status_code=404, detail="Plantilla no encontrada")
    return templates.TemplateResponse("plantilla_detail.html", {"request": request, "plantilla": plantilla})

@app.get("/torneos/{id}", response_class=HTMLResponse)
async def get_torneo(request: Request, id: int):
    torneos = load_torneos()
    torneo = next((t for t in torneos if t.id == id), None)
    if not torneo:
        raise HTTPException(status_code=404, detail="Torneo no encontrado")
    return templates.TemplateResponse("torneo_detail.html", {"request": request, "torneo": torneo})

# Rutas para crear
@app.get("/equipos/crear/", response_class=HTMLResponse)
async def create_equipo_form(request: Request):
    return templates.TemplateResponse("equipos_crear.html", {"request": request})

@app.post("/equipos/crear/", response_class=HTMLResponse)
async def create_equipo(
    id: int = Form(...), nombre: str = Form(...), pais: str = Form(...),
    enfrentamientos_con_colombia: int = Form(...)
):
    equipos = load_equipos()
    new_equipo = Equipo(id=id, nombre=nombre, pais=pais, enfrentamientos_con_colombia=enfrentamientos_con_colombia)
    update_csv(equipos, EQUIPOS_CSV, new_equipo)
    return RedirectResponse(url="/equipos/", status_code=303)

@app.get("/jugadores/crear/", response_class=HTMLResponse)
async def create_jugador_form(request: Request):
    return templates.TemplateResponse("jugadores_crear.html", {"request": request})

@app.post("/jugadores/crear/", response_class=HTMLResponse)
async def create_jugador(
    id: int = Form(...), Jugadores: str = Form(...), F_Nacim_Edad: str = Form(...),
    Club: str = Form(...), Altura: str = Form(...), Pie: str = Form(...),
    Partidos_con_la_seleccion: int = Form(...), Goles: int = Form(...),
    Numero_de_camisa: int = Form(...), anio: int = Form(...), posicion: str = Form(...),
    activo: bool = Form(...), imagen: Optional[str] = Form(None)
):
    jugadores = load_jugadores()
    new_jugador = Jugador(id=id, Jugadores=Jugadores, F_Nacim_Edad=F_Nacim_Edad, Club=Club, Altura=Altura, Pie=Pie,
                          Partidos_con_la_seleccion=Partidos_con_la_seleccion, Goles=Goles, Numero_de_camisa=Numero_de_camisa,
                          anio=anio, posicion=posicion, activo=activo, imagen=imagen)
    update_csv(jugadores, JUGADORES_CSV, new_jugador)
    return RedirectResponse(url="/jugadores/", status_code=303)

@app.get("/partidos/crear/", response_class=HTMLResponse)
async def create_partido_form(request: Request):
    return templates.TemplateResponse("partidos_crear.html", {"request": request})

@app.post("/partidos/crear/", response_class=HTMLResponse)
async def create_partido(
    id: int = Form(...), equipo_local: str = Form(...), equipo_visitante: str = Form(...),
    fecha: str = Form(...), goles_local: int = Form(...), goles_visitante: int = Form(...),
    torneo_id: int = Form(...), eliminado: Optional[str] = Form(None), tarjetas_amarillas_local: int = Form(...),
    tarjetas_amarillas_visitante: int = Form(...), tarjetas_rojas_local: int = Form(...),
    tarjetas_rojas_visitante: int = Form(...)
):
    partidos = load_partidos()
    new_partido = Partido(id=id, equipo_local=equipo_local, equipo_visitante=equipo_visitante, fecha=fecha,
                          goles_local=goles_local, goles_visitante=goles_visitante, torneo_id=torneo_id,
                          eliminado=eliminado, tarjetas_amarillas_local=tarjetas_amarillas_local,
                          tarjetas_amarillas_visitante=tarjetas_amarillas_visitante,
                          tarjetas_rojas_local=tarjetas_rojas_local,
                          tarjetas_rojas_visitante=tarjetas_rojas_visitante)
    update_csv(partidos, PARTIDOS_CSV, new_partido)
    return RedirectResponse(url="/partidos/", status_code=303)

@app.get("/plantillas/crear/", response_class=HTMLResponse)
async def create_plantilla_form(request: Request):
    return templates.TemplateResponse("plantillas_crear.html", {"request": request})

@app.post("/plantillas/crear/", response_class=HTMLResponse)
async def create_plantilla(
    id: int = Form(...), equipo_id: int = Form(...), nombre: Optional[str] = Form(None),
    posicion: Optional[str] = Form(None), anio: Optional[int] = Form(None), torneo_id: Optional[int] = Form(None),
    jugador_id: Optional[int] = Form(None)
):
    plantillas = load_plantillas()
    new_plantilla = Plantilla(id=id, equipo_id=equipo_id, nombre=nombre, posicion=posicion,
                              anio=anio, torneo_id=torneo_id, jugador_id=jugador_id)
    update_csv(plantillas, PLANTILLA_CSV, new_plantilla)
    return RedirectResponse(url="/plantillas/", status_code=303)

@app.get("/torneos/crear/", response_class=HTMLResponse)
async def create_torneo_form(request: Request):
    return templates.TemplateResponse("torneos_crear.html", {"request": request})

@app.post("/torneos/crear/", response_class=HTMLResponse)
async def create_torneo(
    id: int = Form(...), nombre: str = Form(...), anio: int = Form(...),
    pais_anfitrion: Optional[str] = Form(None), estado: str = Form(...), eliminado: Optional[str] = Form(None)
):
    torneos = load_torneos()
    new_torneo = Torneo(id=id, nombre=nombre, anio=anio, pais_anfitrion=pais_anfitrion,
                        estado=estado, eliminado=eliminado)
    update_csv(torneos, TORNEOS_CSV, new_torneo)
    return RedirectResponse(url="/torneos/", status_code=303)

# Rutas para editar
@app.get("/equipos/{id}/edit", response_class=HTMLResponse)
async def edit_equipo_form(request: Request, id: int):
    equipos = load_equipos()
    equipo = next((e for e in equipos if e.id == id), None)
    if not equipo:
        raise HTTPException(status_code=404, detail="Equipo no encontrado")
    return templates.TemplateResponse("equipos_edit.html", {"request": request, "equipo": equipo})

@app.post("/equipos/{id}/edit", response_class=HTMLResponse)
async def edit_equipo(id: int, nombre: str = Form(...), pais: str = Form(...), enfrentamientos_con_colombia: int = Form(...)):
    equipos = load_equipos()
    new_equipo = Equipo(id=id, nombre=nombre, pais=pais, enfrentamientos_con_colombia=enfrentamientos_con_colombia)
    update_csv(equipos, EQUIPOS_CSV, new_equipo)
    return RedirectResponse(url="/equipos/", status_code=303)

@app.get("/jugadores/{id}/edit", response_class=HTMLResponse)
async def edit_jugador_form(request: Request, id: int):
    jugadores = load_jugadores()
    jugador = next((j for j in jugadores if j.id == id), None)
    if not jugador:
        raise HTTPException(status_code=404, detail="Jugador no encontrado")
    return templates.TemplateResponse("jugadores_edit.html", {"request": request, "jugador": jugador})

@app.post("/jugadores/{id}/edit", response_class=HTMLResponse)
async def edit_jugador(id: int, Jugadores: str = Form(...), F_Nacim_Edad: str = Form(...), Club: str = Form(...), Altura: str = Form(...), Pie: str = Form(...), Partidos_con_la_seleccion: int = Form(...), Goles: int = Form(...), Numero_de_camisa: int = Form(...), anio: int = Form(...), posicion: str = Form(...), activo: bool = Form(...), imagen: Optional[str] = Form(None)):
    jugadores = load_jugadores()
    new_jugador = Jugador(id=id, Jugadores=Jugadores, F_Nacim_Edad=F_Nacim_Edad, Club=Club, Altura=Altura, Pie=Pie, Partidos_con_la_seleccion=Partidos_con_la_seleccion, Goles=Goles, Numero_de_camisa=Numero_de_camisa, anio=anio, posicion=posicion, activo=activo, imagen=imagen)
    update_csv(jugadores, JUGADORES_CSV, new_jugador)
    return RedirectResponse(url="/jugadores/", status_code=303)

@app.get("/partidos/{id}/edit", response_class=HTMLResponse)
async def edit_partido_form(request: Request, id: int):
    partidos = load_partidos()
    partido = next((p for p in partidos if p.id == id), None)
    if not partido:
        raise HTTPException(status_code=404, detail="Partido no encontrado")
    return templates.TemplateResponse("partidos_edit.html", {"request": request, "partido": partido})

@app.post("/partidos/{id}/edit", response_class=HTMLResponse)
async def edit_partido(id: int, equipo_local: str = Form(...), equipo_visitante: str = Form(...), fecha: str = Form(...), goles_local: int = Form(...), goles_visitante: int = Form(...), torneo_id: int = Form(...), eliminado: Optional[str] = Form(None), tarjetas_amarillas_local: int = Form(...), tarjetas_amarillas_visitante: int = Form(...), tarjetas_rojas_local: int = Form(...), tarjetas_rojas_visitante: int = Form(...)):
    partidos = load_partidos()
    new_partido = Partido(id=id, equipo_local=equipo_local, equipo_visitante=equipo_visitante, fecha=fecha, goles_local=goles_local, goles_visitante=goles_visitante, torneo_id=torneo_id, eliminado=eliminado, tarjetas_amarillas_local=tarjetas_amarillas_local, tarjetas_amarillas_visitante=tarjetas_amarillas_visitante, tarjetas_rojas_local=tarjetas_rojas_local, tarjetas_rojas_visitante=tarjetas_rojas_visitante)
    update_csv(partidos, PARTIDOS_CSV, new_partido)
    return RedirectResponse(url="/partidos/", status_code=303)

@app.get("/plantillas/{id}/edit", response_class=HTMLResponse)
async def edit_plantilla_form(request: Request, id: int):
    plantillas = load_plantillas()
    plantilla = next((p for p in plantillas if p.id == id), None)
    if not plantilla:
        raise HTTPException(status_code=404, detail="Plantilla no encontrada")
    return templates.TemplateResponse("plantillas_edit.html", {"request": request, "plantilla": plantilla})

@app.post("/plantillas/{id}/edit", response_class=HTMLResponse)
async def edit_plantilla(id: int, equipo_id: int = Form(...), nombre: Optional[str] = Form(None), posicion: Optional[str] = Form(None), anio: Optional[int] = Form(None), torneo_id: Optional[int] = Form(None), jugador_id: Optional[int] = Form(None)):
    plantillas = load_plantillas()
    new_plantilla = Plantilla(id=id, equipo_id=equipo_id, nombre=nombre, posicion=posicion, anio=anio, torneo_id=torneo_id, jugador_id=jugador_id)
    update_csv(plantillas, PLANTILLA_CSV, new_plantilla)
    return RedirectResponse(url="/plantillas/", status_code=303)

@app.get("/torneos/{id}/edit", response_class=HTMLResponse)
async def edit_torneo_form(request: Request, id: int):
    torneos = load_torneos()
    torneo = next((t for t in torneos if t.id == id), None)
    if not torneo:
        raise HTTPException(status_code=404, detail="Torneo no encontrado")
    return templates.TemplateResponse("torneos_edit.html", {"request": request, "torneo": torneo})

@app.post("/torneos/{id}/edit", response_class=HTMLResponse)
async def edit_torneo(id: int, nombre: str = Form(...), anio: int = Form(...), pais_anfitrion: Optional[str] = Form(None), estado: str = Form(...), eliminado: Optional[str] = Form(None)):
    torneos = load_torneos()
    new_torneo = Torneo(id=id, nombre=nombre, anio=anio, pais_anfitrion=pais_anfitrion, estado=estado, eliminado=eliminado)
    update_csv(torneos, TORNEOS_CSV, new_torneo)
    return RedirectResponse(url="/torneos/", status_code=303)

# Rutas para eliminar
@app.get("/equipos/{id}/delete", response_class=HTMLResponse)
async def delete_equipo(request: Request, id: int):
    equipos = load_equipos()
    equipos = delete_from_csv(equipos, EQUIPOS_CSV, id)
    return RedirectResponse(url="/equipos/", status_code=303)

@app.get("/jugadores/{id}/delete", response_class=HTMLResponse)
async def delete_jugador(request: Request, id: int):
    jugadores = load_jugadores()
    jugadores = delete_from_csv(jugadores, JUGADORES_CSV, id)
    return RedirectResponse(url="/jugadores/", status_code=303)

@app.get("/partidos/{id}/delete", response_class=HTMLResponse)
async def delete_partido(request: Request, id: int):
    partidos = load_partidos()
    partidos = delete_from_csv(partidos, PARTIDOS_CSV, id)
    return RedirectResponse(url="/partidos/", status_code=303)

@app.get("/plantillas/{id}/delete", response_class=HTMLResponse)
async def delete_plantilla(request: Request, id: int):
    plantillas = load_plantillas()
    plantillas = delete_from_csv(plantillas, PLANTILLA_CSV, id)
    return RedirectResponse(url="/plantillas/", status_code=303)

@app.get("/torneos/{id}/delete", response_class=HTMLResponse)
async def delete_torneo(request: Request, id: int):
    torneos = load_torneos()
    torneos = delete_from_csv(torneos, TORNEOS_CSV, id)
    return RedirectResponse(url="/torneos/", status_code=303)