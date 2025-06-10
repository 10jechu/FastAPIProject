from fastapi import FastAPI, Request, HTTPException, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
import pandas as pd
from pydantic import BaseModel, ValidationError, validator
from typing import Optional
import os
import shutil
from datetime import datetime

app = FastAPI()
templates = Jinja2Templates(directory="templates")

# Rutas de los archivos CSV
DATA_DIR = "data"
CSV_FILES = {
    "jugadores": os.path.join(DATA_DIR, "jugadores.csv"),
    "equipos": os.path.join(DATA_DIR, "equipos.csv"),
    "partidos": os.path.join(DATA_DIR, "partidos.csv"),
    "torneos": os.path.join(DATA_DIR, "torneos.csv"),
    "history": {
        "jugadores": os.path.join(DATA_DIR, "jugadores_history.csv"),
        "equipos": os.path.join(DATA_DIR, "equipos_history.csv"),
        "partidos": os.path.join(DATA_DIR, "partidos_history.csv"),
        "torneos": os.path.join(DATA_DIR, "torneos_history.csv")
    },
    "trash": {
        "jugadores": os.path.join(DATA_DIR, "jugadores_trash.csv")
    }
}

# Modelos Pydantic
class Jugador(BaseModel):
    id: int
    nombre: str
    fecha_nacimiento: str
    club: Optional[str] = None
    altura: Optional[str] = None
    pie: Optional[str] = None
    partidos: int
    goles: int
    numero_camisa: int
    anio: int
    posicion: str
    activo: bool
    imagen: Optional[str] = None

    @validator('anio')
    def anio_must_be_between_2021_and_2025(cls, v):
        if not 2021 <= v <= 2025:
            raise ValueError('El año debe estar entre 2021 y 2025')
        return v

class Equipo(BaseModel):
    id: int
    nombre: str
    pais: str
    enfrentamientos_con_colombia: int
    bandera: Optional[str] = None

class Partido(BaseModel):
    id: int
    fecha: str
    equipo_local: str
    equipo_visitante: str
    goles_local: int
    goles_visitante: int
    torneo_id: Optional[int] = None
    eliminado: Optional[str] = None
    tarjetas_amarillas_local: int = 0
    tarjetas_amarillas_visitante: int = 0
    tarjetas_rojas_local: int = 0
    tarjetas_rojas_visitante: int = 0

    @validator('fecha')
    def fecha_valida(cls, v):
        try:
            datetime.strptime(v, '%Y-%m-%d')
            return v
        except ValueError:
            raise ValueError('La fecha debe estar en formato YYYY-MM-DD')

class Torneo(BaseModel):
    id: int
    nombre: str
    anio: int
    pais_anfitrion: Optional[str] = None
    estado: Optional[str] = None
    eliminado: Optional[str] = None
    imagen: Optional[str] = None

    @validator('anio')
    def anio_must_be_between_2021_and_2025(cls, v):
        if not 2021 <= v <= 2025:
            raise ValueError('El año debe estar entre 2021 y 2025')
        return v

# Funciones de carga y guardado
def load_data(file_path, model_class):
    if os.path.exists(file_path):
        df = pd.read_csv(file_path)
        return [model_class(**row) for _, row in df.iterrows()]
    return []

def save_data(file_path, data):
    df = pd.DataFrame([item.dict() for item in data])
    df.to_csv(file_path, index=False)

def load_jugadores():
    return load_data(CSV_FILES["jugadores"], Jugador)

def load_equipos():
    return load_data(CSV_FILES["equipos"], Equipo)

def load_partidos():
    return load_data(CSV_FILES["partidos"], Partido)

def load_torneos():
    return load_data(CSV_FILES["torneos"], Torneo)

def log_action(file_path, action, data):
    if not os.path.exists(file_path):
        pd.DataFrame(columns=["timestamp", "action", "data"]).to_csv(file_path, index=False)
    df = pd.read_csv(file_path)
    new_entry = pd.DataFrame({"timestamp": [datetime.now().strftime('%Y-%m-%d %H:%M:%S')], "action": [action], "data": [str(data)]})
    df = pd.concat([df, new_entry], ignore_index=True)
    df.to_csv(file_path, index=False)

def move_to_trash(model, id_field):
    data = load_data(CSV_FILES[model], globals()[model.capitalize()])
    item = next((d for d in data if getattr(d, id_field) == id_field), None)
    if item:
        trash_data = load_data(CSV_FILES["trash"][model], globals()[model.capitalize()])
        trash_data.append(item)
        save_data(CSV_FILES["trash"][model], trash_data)
        data = [d for d in data if getattr(d, id_field) != id_field]
        save_data(CSV_FILES[model], data)
        log_action(CSV_FILES["history"][model], "delete", item.dict())

# Rutas
@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.get("/jugadores/", response_class=HTMLResponse)
async def get_jugadores(request: Request, year: Optional[int] = None):
    jugadores = load_jugadores()
    if year:
        jugadores = [j for j in jugadores if j.anio == year]
    return templates.TemplateResponse("jugadores.html", {"request": request, "jugadores": jugadores, "year": year})

@app.get("/jugadores/crear/", response_class=HTMLResponse)
async def create_jugador_form(request: Request):
    return templates.TemplateResponse("jugadores_crear.html", {"request": request})

@app.post("/jugadores/crear/", response_class=HTMLResponse)
async def create_jugador(
    request: Request,
    nombre: str = Form(...),
    fecha_nacimiento: str = Form(...),
    club: str = Form(None),
    altura: str = Form(None),
    pie: str = Form(None),
    partidos: int = Form(...),
    goles: int = Form(...),
    numero_camisa: int = Form(...),
    anio: int = Form(...),
    posicion: str = Form(...),
    activo: bool = Form(...),
    imagen: str = Form(None)
):
    jugadores = load_jugadores()
    new_id = max([j.id for j in jugadores] + [0]) + 1
    nuevo_jugador = Jugador(
        id=new_id, nombre=nombre, fecha_nacimiento=fecha_nacimiento, club=club,
        altura=altura, pie=pie, partidos=partidos, goles=goles, numero_camisa=numero_camisa,
        anio=anio, posicion=posicion, activo=activo, imagen=imagen
    )
    jugadores.append(nuevo_jugador)
    save_data(CSV_FILES["jugadores"], jugadores)
    log_action(CSV_FILES["history"]["jugadores"], "create", nuevo_jugador.dict())
    return RedirectResponse(url="/jugadores/", status_code=303)

@app.get("/jugadores/{id}/edit/", response_class=HTMLResponse)
async def edit_jugador_form(request: Request, id: int):
    jugadores = load_jugadores()
    jugador = next((j for j in jugadores if j.id == id), None)
    if not jugador:
        raise HTTPException(status_code=404, detail="Jugador no encontrado")
    return templates.TemplateResponse("jugadores_edit.html", {"request": request, "jugador": jugador})

@app.post("/jugadores/{id}/edit/", response_class=HTMLResponse)
async def edit_jugador(
    id: int,
    request: Request,
    nombre: str = Form(...),
    fecha_nacimiento: str = Form(...),
    club: str = Form(None),
    altura: str = Form(None),
    pie: str = Form(None),
    partidos: int = Form(...),
    goles: int = Form(...),
    numero_camisa: int = Form(...),
    anio: int = Form(...),
    posicion: str = Form(...),
    activo: bool = Form(...),
    imagen: str = Form(None)
):
    jugadores = load_jugadores()
    jugador = next((j for j in jugadores if j.id == id), None)
    if not jugador:
        raise HTTPException(status_code=404, detail="Jugador no encontrado")
    jugador_idx = jugadores.index(jugador)
    updated_jugador = Jugador(
        id=id, nombre=nombre, fecha_nacimiento=fecha_nacimiento, club=club,
        altura=altura, pie=pie, partidos=partidos, goles=goles, numero_camisa=numero_camisa,
        anio=anio, posicion=posicion, activo=activo, imagen=imagen
    )
    jugadores[jugador_idx] = updated_jugador
    save_data(CSV_FILES["jugadores"], jugadores)
    log_action(CSV_FILES["history"]["jugadores"], "update", updated_jugador.dict())
    return RedirectResponse(url="/jugadores/", status_code=303)

@app.get("/jugadores/{id}/delete/", response_class=HTMLResponse)
async def delete_jugador(request: Request, id: int):
    move_to_trash("jugadores", id)
    return RedirectResponse(url="/jugadores/", status_code=303)

@app.get("/equipos/", response_class=HTMLResponse)
async def get_equipos(request: Request, year: Optional[int] = None):
    equipos = load_equipos()
    if year:
        equipos = [e for e in equipos if any(p.anio == year for p in load_partidos() if e.nombre in [p.equipo_local, p.equipo_visitante])]
    return templates.TemplateResponse("equipos.html", {"request": request, "equipos": equipos, "year": year})

@app.get("/equipos/crear/", response_class=HTMLResponse)
async def create_equipo_form(request: Request):
    return templates.TemplateResponse("equipos_crear.html", {"request": request})

@app.post("/equipos/crear/", response_class=HTMLResponse)
async def create_equipo(
    request: Request,
    nombre: str = Form(...),
    pais: str = Form(...),
    enfrentamientos_con_colombia: int = Form(...),
    bandera: str = Form(None)
):
    equipos = load_equipos()
    new_id = max([e.id for e in equipos] + [0]) + 1
    nuevo_equipo = Equipo(id=new_id, nombre=nombre, pais=pais, enfrentamientos_con_colombia=enfrentamientos_con_colombia, bandera=bandera)
    equipos.append(nuevo_equipo)
    save_data(CSV_FILES["equipos"], equipos)
    log_action(CSV_FILES["history"]["equipos"], "create", nuevo_equipo.dict())
    return RedirectResponse(url="/equipos/", status_code=303)

@app.get("/equipos/{id}/edit/", response_class=HTMLResponse)
async def edit_equipo_form(request: Request, id: int):
    equipos = load_equipos()
    equipo = next((e for e in equipos if e.id == id), None)
    if not equipo:
        raise HTTPException(status_code=404, detail="Equipo no encontrado")
    return templates.TemplateResponse("equipos_edit.html", {"request": request, "equipo": equipo})

@app.post("/equipos/{id}/edit/", response_class=HTMLResponse)
async def edit_equipo(
    id: int,
    request: Request,
    nombre: str = Form(...),
    pais: str = Form(...),
    enfrentamientos_con_colombia: int = Form(...),
    bandera: str = Form(None)
):
    equipos = load_equipos()
    equipo = next((e for e in equipos if e.id == id), None)
    if not equipo:
        raise HTTPException(status_code=404, detail="Equipo no encontrado")
    equipo_idx = equipos.index(equipo)
    updated_equipo = Equipo(id=id, nombre=nombre, pais=pais, enfrentamientos_con_colombia=enfrentamientos_con_colombia, bandera=bandera)
    equipos[equipo_idx] = updated_equipo
    save_data(CSV_FILES["equipos"], equipos)
    log_action(CSV_FILES["history"]["equipos"], "update", updated_equipo.dict())
    return RedirectResponse(url="/equipos/", status_code=303)

@app.get("/equipos/{id}/delete/", response_class=HTMLResponse)
async def delete_equipo(request: Request, id: int):
    move_to_trash("equipos", id)
    return RedirectResponse(url="/equipos/", status_code=303)

@app.get("/partidos/", response_class=HTMLResponse)
async def get_partidos(request: Request, year: Optional[int] = None):
    partidos = load_partidos()
    if year:
        partidos = [p for p in partidos if p.fecha and int(p.fecha.split('-')[0]) == year]
    return templates.TemplateResponse("partidos.html", {"request": request, "partidos": partidos, "year": year, "torneos_dict": {t.id: t for t in load_torneos()}})

@app.get("/partidos/crear/", response_class=HTMLResponse)
async def create_partido_form(request: Request):
    return templates.TemplateResponse("partidos_crear.html", {"request": request})

@app.post("/partidos/crear/", response_class=HTMLResponse)
async def create_partido(
    request: Request,
    fecha: str = Form(...),
    equipo_local: str = Form(...),
    equipo_visitante: str = Form(...),
    goles_local: int = Form(...),
    goles_visitante: int = Form(...),
    torneo_id: Optional[int] = Form(None),
    eliminado: str = Form(None),
    tarjetas_amarillas_local: int = Form(0),
    tarjetas_amarillas_visitante: int = Form(0),
    tarjetas_rojas_local: int = Form(0),
    tarjetas_rojas_visitante: int = Form(0)
):
    partidos = load_partidos()
    new_id = max([p.id for p in partidos] + [0]) + 1
    nuevo_partido = Partido(
        id=new_id, fecha=fecha, equipo_local=equipo_local, equipo_visitante=equipo_visitante,
        goles_local=goles_local, goles_visitante=goles_visitante, torneo_id=torneo_id,
        eliminado=eliminado, tarjetas_amarillas_local=tarjetas_amarillas_local,
        tarjetas_amarillas_visitante=tarjetas_amarillas_visitante,
        tarjetas_rojas_local=tarjetas_rojas_local, tarjetas_rojas_visitante=tarjetas_rojas_visitante
    )
    partidos.append(nuevo_partido)
    save_data(CSV_FILES["partidos"], partidos)
    log_action(CSV_FILES["history"]["partidos"], "create", nuevo_partido.dict())
    return RedirectResponse(url="/partidos/", status_code=303)

@app.get("/partidos/{id}/edit/", response_class=HTMLResponse)
async def edit_partido_form(request: Request, id: int):
    partidos = load_partidos()
    partido = next((p for p in partidos if p.id == id), None)
    if not partido:
        raise HTTPException(status_code=404, detail="Partido no encontrado")
    return templates.TemplateResponse("partidos_edit.html", {"request": request, "partido": partido})

@app.post("/partidos/{id}/edit/", response_class=HTMLResponse)
async def edit_partido(
    id: int,
    request: Request,
    fecha: str = Form(...),
    equipo_local: str = Form(...),
    equipo_visitante: str = Form(...),
    goles_local: int = Form(...),
    goles_visitante: int = Form(...),
    torneo_id: Optional[int] = Form(None),
    eliminado: str = Form(None),
    tarjetas_amarillas_local: int = Form(0),
    tarjetas_amarillas_visitante: int = Form(0),
    tarjetas_rojas_local: int = Form(0),
    tarjetas_rojas_visitante: int = Form(0)
):
    partidos = load_partidos()
    partido = next((p for p in partidos if p.id == id), None)
    if not partido:
        raise HTTPException(status_code=404, detail="Partido no encontrado")
    partido_idx = partidos.index(partido)
    updated_partido = Partido(
        id=id, fecha=fecha, equipo_local=equipo_local, equipo_visitante=equipo_visitante,
        goles_local=goles_local, goles_visitante=goles_visitante, torneo_id=torneo_id,
        eliminado=eliminado, tarjetas_amarillas_local=tarjetas_amarillas_local,
        tarjetas_amarillas_visitante=tarjetas_amarillas_visitante,
        tarjetas_rojas_local=tarjetas_rojas_local, tarjetas_rojas_visitante=tarjetas_rojas_visitante
    )
    partidos[partido_idx] = updated_partido
    save_data(CSV_FILES["partidos"], partidos)
    log_action(CSV_FILES["history"]["partidos"], "update", updated_partido.dict())
    return RedirectResponse(url="/partidos/", status_code=303)

@app.get("/partidos/{id}/delete/", response_class=HTMLResponse)
async def delete_partido(request: Request, id: int):
    move_to_trash("partidos", id)
    return RedirectResponse(url="/partidos/", status_code=303)

@app.get("/torneos/", response_class=HTMLResponse)
async def get_torneos(request: Request, year: Optional[int] = None):
    torneos = load_torneos()
    if year:
        torneos = [t for t in torneos if t.anio == year]
    return templates.TemplateResponse("torneos.html", {"request": request, "torneos": torneos, "year": year})

@app.get("/torneos/crear/", response_class=HTMLResponse)
async def create_torneo_form(request: Request):
    return templates.TemplateResponse("torneos_crear.html", {"request": request})

@app.post("/torneos/crear/", response_class=HTMLResponse)
async def create_torneo(
    request: Request,
    nombre: str = Form(...),
    anio: int = Form(...),
    pais_anfitrion: str = Form(None),
    estado: str = Form(None),
    eliminado: str = Form(None),
    imagen: str = Form(None)
):
    torneos = load_torneos()
    new_id = max([t.id for t in torneos] + [0]) + 1
    nuevo_torneo = Torneo(id=new_id, nombre=nombre, anio=anio, pais_anfitrion=pais_anfitrion, estado=estado, eliminado=eliminado, imagen=imagen)
    torneos.append(nuevo_torneo)
    save_data(CSV_FILES["torneos"], torneos)
    log_action(CSV_FILES["history"]["torneos"], "create", nuevo_torneo.dict())
    return RedirectResponse(url="/torneos/", status_code=303)

@app.get("/torneos/{id}/edit/", response_class=HTMLResponse)
async def edit_torneo_form(request: Request, id: int):
    torneos = load_torneos()
    torneo = next((t for t in torneos if t.id == id), None)
    if not torneo:
        raise HTTPException(status_code=404, detail="Torneo no encontrado")
    return templates.TemplateResponse("torneos_edit.html", {"request": request, "torneo": torneo})

@app.post("/torneos/{id}/edit/", response_class=HTMLResponse)
async def edit_torneo(
    id: int,
    request: Request,
    nombre: str = Form(...),
    anio: int = Form(...),
    pais_anfitrion: str = Form(None),
    estado: str = Form(None),
    eliminado: str = Form(None),
    imagen: str = Form(None)
):
    torneos = load_torneos()
    torneo = next((t for t in torneos if t.id == id), None)
    if not torneo:
        raise HTTPException(status_code=404, detail="Torneo no encontrado")
    torneo_idx = torneos.index(torneo)
    updated_torneo = Torneo(id=id, nombre=nombre, anio=anio, pais_anfitrion=pais_anfitrion, estado=estado, eliminado=eliminado, imagen=imagen)
    torneos[torneo_idx] = updated_torneo
    save_data(CSV_FILES["torneos"], torneos)
    log_action(CSV_FILES["history"]["torneos"], "update", updated_torneo.dict())
    return RedirectResponse(url="/torneos/", status_code=303)

@app.get("/torneos/{id}/delete/", response_class=HTMLResponse)
async def delete_torneo(request: Request, id: int):
    move_to_trash("torneos", id)
    return RedirectResponse(url="/torneos/", status_code=303)

@app.get("/estadisticas/completa/", response_class=HTMLResponse)
async def get_estadisticas_completa(request: Request):
    jugadores = load_jugadores()
    partidos = load_partidos()
    torneos = load_torneos()
    torneos_dict = {t.id: t for t in torneos}

    victorias_total = 0
    goles_total = 0
    partidos_jugados_total = 0
    victorias_por_anio = {}
    goles_por_anio = {}
    partidos_jugados_por_anio = {}

    for p in partidos:
        try:
            anio = p.fecha.split('-')[0] if p.fecha and '-' in p.fecha else "Sin año"
            if 2021 <= int(anio) <= 2024 and (p.equipo_local.lower() == "colombia" or p.equipo_visitante.lower() == "colombia"):
                partidos_jugados_total += 1
                partidos_jugados_por_anio[anio] = partidos_jugados_por_anio.get(anio, 0) + 1
                goles_colombia = (p.goles_local if p.equipo_local.lower() == "colombia" else 0) + (p.goles_visitante if p.equipo_visitante.lower() == "colombia" else 0)
                goles_total += goles_colombia
                goles_por_anio[anio] = goles_por_anio.get(anio, 0) + goles_colombia
                if (p.equipo_local.lower() == "colombia" and p.goles_local > p.goles_visitante) or (p.equipo_visitante.lower() == "colombia" and p.goles_visitante > p.goles_local):
                    victorias_total += 1
                    victorias_por_anio[anio] = victorias_por_anio.get(anio, 0) + 1
        except (IndexError, AttributeError, ValueError):
            continue

    promedio_goles_total = round(goles_total / partidos_jugados_total, 2) if partidos_jugados_total > 0 else 0
    promedio_goles_por_anio = {anio: round(goles / partidos, 2) for anio, goles in goles_por_anio.items() for partidos in [partidos_jugados_por_anio.get(anio, 1)] if partidos_jugados_por_anio.get(anio, 1) > 0}

    torneos_jugados = {}
    for p in partidos:
        if p.torneo_id and p.torneo_id in torneos_dict and 2021 <= int(p.fecha.split('-')[0]) <= 2024:
            torneos_jugados[p.torneo_id] = torneos_dict[p.torneo_id].nombre

    return templates.TemplateResponse("estadisticas.html", {
        "request": request, "jugadores": jugadores, "partidos": partidos, "torneos": torneos,
        "victorias_total": victorias_total, "goles_total": goles_total, "partidos_jugados_total": partidos_jugados_total,
        "promedio_goles_total": promedio_goles_total, "victorias_por_anio": victorias_por_anio,
        "goles_por_anio": goles_por_anio, "partidos_jugados_por_anio": partidos_jugados_por_anio,
        "promedio_goles_por_anio": promedio_goles_por_anio, "torneos_dict": torneos_dict,
        "torneos_jugados": torneos_jugados
    })

@app.get("/documentacion/", response_class=HTMLResponse)
async def get_documentacion(request: Request):
    return templates.TemplateResponse("documentacion.html", {"request": request})

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)