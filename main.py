from fastapi import FastAPI, Request, Form, Depends, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel, ValidationError, Field
from typing import List, Optional
import pandas as pd
import csv
import os

app = FastAPI()
templates = Jinja2Templates(directory="templates")

# Rutas de los archivos CSV
JUGADORES_CSV = "data/jugadores.csv"
EQUIPOS_CSV = "data/equipos.csv"
PARTIDOS_CSV = "data/partidos.csv"
PLANTILLA_CSV = "data/plantillas.csv"
TORNEOS_CSV = "data/torneos.csv"

# Modelos Pydantic
class Jugador(BaseModel):
    id: int
    Jugadores: str
    F_Nacim_Edad: str
    Club: str
    Altura: str
    Pie: str
    Partidos_con_la_seleccion: int
    Goles: int
    Numero_de_camisa: int
    anio: int
    posicion: str
    activo: bool
    imagen: Optional[str] = None  # Permitir valores nulos

class Equipo(BaseModel):
    id: int
    nombre: str
    pais: str
    enfrentamientos_con_colombia: int

class Partido(BaseModel):
    id: int
    fecha: str
    equipo_local: str
    equipo_visitante: str
    goles_local: int
    goles_visitante: int
    torneo_id: int
    eliminado: str
    tarjetas_amarillas_local: int
    tarjetas_amarillas_visitante: int
    tarjetas_rojas_local: int
    tarjetas_rojas_visitante: int

class Plantilla(BaseModel):
    id: int
    equipo_id: int
    jugador_id: int

class Torneo(BaseModel):
    id: int
    nombre: str
    anio: int
    eliminado: str

# Funciones de carga y actualización de datos
def load_csv(csv_file):
    if not os.path.exists(csv_file):
        return []
    df = pd.read_csv(csv_file)
    return df.to_dict(orient="records")

def update_csv(data_list, csv_file, new_item):
    data_dicts = [item.dict(exclude_unset=True) for item in data_list]
    if isinstance(new_item, Jugador):
        data_dicts.append(new_item.dict(exclude_unset=True))
    elif isinstance(new_item, Equipo):
        data_dicts.append(new_item.dict(exclude_unset=True))
    elif isinstance(new_item, Partido):
        data_dicts.append(new_item.dict(exclude_unset=True))
    elif isinstance(new_item, Plantilla):
        data_dicts.append(new_item.dict(exclude_unset=True))
    elif isinstance(new_item, Torneo):
        data_dicts.append(new_item.dict(exclude_unset=True))
    fieldnames = list(dict.fromkeys([key for item in data_dicts for key in item.keys()]))  # Eliminar duplicados
    with open(csv_file, mode='w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(data_dicts)
    return data_list

def load_jugadores():
    return [Jugador(**item) for item in load_csv(JUGADORES_CSV)]

def load_equipos():
    return [Equipo(**item) for item in load_csv(EQUIPOS_CSV)]

def load_partidos():
    return [Partido(**item) for item in load_csv(PARTIDOS_CSV)]

def load_plantillas():
    return [Plantilla(**item) for item in load_csv(PLANTILLA_CSV)]

def load_torneos():
    return [Torneo(**item) for item in load_csv(TORNEOS_CSV)]

# Rutas para Jugadores
@app.get("/jugadores/", response_class=HTMLResponse)
async def get_jugadores(request: Request):
    jugadores = load_jugadores()
    year = request.query_params.get("year")
    if year:
        jugadores = [j for j in jugadores if str(j.anio) == year]
    return templates.TemplateResponse("jugadores.html", {"request": request, "jugadores": jugadores})

@app.get("/jugadores/crear/", response_class=HTMLResponse)
async def create_jugador_form(request: Request):
    return templates.TemplateResponse("jugadores_crear.html", {"request": request})

@app.post("/jugadores/crear/")
async def create_jugador(
    Jugadores: str = Form(...),
    F_Nacim_Edad: str = Form(...),
    Club: str = Form(...),
    Altura: str = Form(...),
    Pie: str = Form(...),
    Partidos_con_la_seleccion: int = Form(...),
    Goles: int = Form(...),
    Numero_de_camisa: int = Form(...),
    anio: int = Form(...),
    posicion: str = Form(...),
    activo: bool = Form(False),
    imagen: str = Form("")
):
    jugadores = load_jugadores()
    new_id = max([j.id for j in jugadores] + [0]) + 1
    new_jugador = Jugador(
        id=new_id,
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
        activo=activo,
        imagen=imagen if imagen else None
    )
    update_csv(jugadores, JUGADORES_CSV, new_jugador)
    return RedirectResponse(url="/jugadores/", status_code=303)

@app.get("/jugadores/{id}/edit", response_class=HTMLResponse)
async def edit_jugador_form(request: Request, id: int):
    jugadores = load_jugadores()
    jugador = next((j for j in jugadores if j.id == id), None)
    if not jugador:
        raise HTTPException(status_code=404, detail="Jugador no encontrado")
    return templates.TemplateResponse("jugadores_edit.html", {"request": request, "jugador": jugador})

@app.post("/jugadores/{id}/update")
async def update_jugador(
    id: int,
    Jugadores: str = Form(...),
    F_Nacim_Edad: str = Form(...),
    Club: str = Form(...),
    Altura: str = Form(...),
    Pie: str = Form(...),
    Partidos_con_la_seleccion: int = Form(...),
    Goles: int = Form(...),
    Numero_de_camisa: int = Form(...),
    anio: int = Form(...),
    posicion: str = Form(...),
    activo: bool = Form(False),
    imagen: str = Form("")
):
    jugadores = load_jugadores()
    jugador = next((j for j in jugadores if j.id == id), None)
    if not jugador:
        raise HTTPException(status_code=404, detail="Jugador no encontrado")
    jugador.Jugadores = Jugadores
    jugador.F_Nacim_Edad = F_Nacim_Edad
    jugador.Club = Club
    jugador.Altura = Altura
    jugador.Pie = Pie
    jugador.Partidos_con_la_seleccion = Partidos_con_la_seleccion
    jugador.Goles = Goles
    jugador.Numero_de_camisa = Numero_de_camisa
    jugador.anio = anio
    jugador.posicion = posicion
    jugador.activo = activo
    jugador.imagen = imagen if imagen else None
    update_csv(jugadores, JUGADORES_CSV, jugador)
    return RedirectResponse(url="/jugadores/", status_code=303)

@app.get("/jugadores/{id}/delete")
async def delete_jugador(id: int):
    jugadores = load_jugadores()
    jugador = next((j for j in jugadores if j.id == id), None)
    if jugador:
        jugadores = [j for j in jugadores if j.id != id]
        update_csv(jugadores, JUGADORES_CSV, jugador)  # Usar un objeto vacío o el último estado
    return RedirectResponse(url="/jugadores/", status_code=303)

# Rutas para Equipos
@app.get("/equipos/", response_class=HTMLResponse)
async def get_equipos(request: Request):
    equipos = load_equipos()
    year = request.query_params.get("year")
    if year:
        equipos = [e for e in equipos if any(str(j.anio) == year for j in load_jugadores() if j.Club == e.nombre)]
    return templates.TemplateResponse("equipos.html", {"request": request, "equipos": equipos})

@app.get("/equipos/crear/", response_class=HTMLResponse)
async def create_equipo_form(request: Request):
    return templates.TemplateResponse("equipos_crear.html", {"request": request})

@app.post("/equipos/crear/")
async def create_equipo(
    nombre: str = Form(...),
    pais: str = Form(...),
    enfrentamientos_con_colombia: int = Form(...)
):
    equipos = load_equipos()
    new_id = max([e.id for e in equipos] + [0]) + 1
    new_equipo = Equipo(
        id=new_id,
        nombre=nombre,
        pais=pais,
        enfrentamientos_con_colombia=enfrentamientos_con_colombia
    )
    update_csv(equipos, EQUIPOS_CSV, new_equipo)
    return RedirectResponse(url="/equipos/", status_code=303)

@app.get("/equipos/{id}/edit", response_class=HTMLResponse)
async def edit_equipo_form(request: Request, id: int):
    equipos = load_equipos()
    equipo = next((e for e in equipos if e.id == id), None)
    if not equipo:
        raise HTTPException(status_code=404, detail="Equipo no encontrado")
    return templates.TemplateResponse("equipos_edit.html", {"request": request, "equipo": equipo})

@app.post("/equipos/{id}/update")
async def update_equipo(
    id: int,
    nombre: str = Form(...),
    pais: str = Form(...),
    enfrentamientos_con_colombia: int = Form(...)
):
    equipos = load_equipos()
    equipo = next((e for e in equipos if e.id == id), None)
    if not equipo:
        raise HTTPException(status_code=404, detail="Equipo no encontrado")
    equipo.nombre = nombre
    equipo.pais = pais
    equipo.enfrentamientos_con_colombia = enfrentamientos_con_colombia
    update_csv(equipos, EQUIPOS_CSV, equipo)
    return RedirectResponse(url="/equipos/", status_code=303)

@app.get("/equipos/{id}/delete")
async def delete_equipo(id: int):
    equipos = load_equipos()
    equipo = next((e for e in equipos if e.id == id), None)
    if equipo:
        equipos = [e for e in equipos if e.id != id]
        update_csv(equipos, EQUIPOS_CSV, equipo)
    return RedirectResponse(url="/equipos/", status_code=303)

# Rutas para Partidos
@app.get("/partidos/", response_class=HTMLResponse)
async def get_partidos(request: Request):
    partidos = load_partidos()
    torneos = load_torneos()
    year = request.query_params.get("year")
    if year:
        partidos = [p for p in partidos if any(t.anio == int(year) for t in torneos if t.id == p.torneo_id)]
    return templates.TemplateResponse("partidos.html", {"request": request, "partidos": partidos, "torneos": torneos})

@app.get("/partidos/crear/", response_class=HTMLResponse)
async def create_partido_form(request: Request):
    return templates.TemplateResponse("partidos_crear.html", {"request": request})

@app.post("/partidos/crear/")
async def create_partido(
    fecha: str = Form(...),
    equipo_local: str = Form(...),
    equipo_visitante: str = Form(...),
    goles_local: int = Form(...),
    goles_visitante: int = Form(...),
    torneo_id: int = Form(...),
    eliminado: str = Form(...),
    tarjetas_amarillas_local: int = Form(0),
    tarjetas_amarillas_visitante: int = Form(0),
    tarjetas_rojas_local: int = Form(0),
    tarjetas_rojas_visitante: int = Form(0)
):
    partidos = load_partidos()
    new_id = max([p.id for p in partidos] + [0]) + 1
    new_partido = Partido(
        id=new_id,
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
    update_csv(partidos, PARTIDOS_CSV, new_partido)
    return RedirectResponse(url="/partidos/", status_code=303)

@app.get("/partidos/{id}/edit", response_class=HTMLResponse)
async def edit_partido_form(request: Request, id: int):
    partidos = load_partidos()
    partido = next((p for p in partidos if p.id == id), None)
    if not partido:
        raise HTTPException(status_code=404, detail="Partido no encontrado")
    return templates.TemplateResponse("partidos_edit.html", {"request": request, "partido": partido})

@app.post("/partidos/{id}/update")
async def update_partido(
    id: int,
    fecha: str = Form(...),
    equipo_local: str = Form(...),
    equipo_visitante: str = Form(...),
    goles_local: int = Form(...),
    goles_visitante: int = Form(...),
    torneo_id: int = Form(...),
    eliminado: str = Form(...),
    tarjetas_amarillas_local: int = Form(0),
    tarjetas_amarillas_visitante: int = Form(0),
    tarjetas_rojas_local: int = Form(0),
    tarjetas_rojas_visitante: int = Form(0)
):
    partidos = load_partidos()
    partido = next((p for p in partidos if p.id == id), None)
    if not partido:
        raise HTTPException(status_code=404, detail="Partido no encontrado")
    partido.fecha = fecha
    partido.equipo_local = equipo_local
    partido.equipo_visitante = equipo_visitante
    partido.goles_local = goles_local
    partido.goles_visitante = goles_visitante
    partido.torneo_id = torneo_id
    partido.eliminado = eliminado
    partido.tarjetas_amarillas_local = tarjetas_amarillas_local
    partido.tarjetas_amarillas_visitante = tarjetas_amarillas_visitante
    partido.tarjetas_rojas_local = tarjetas_rojas_local
    partido.tarjetas_rojas_visitante = tarjetas_rojas_visitante
    update_csv(partidos, PARTIDOS_CSV, partido)
    return RedirectResponse(url="/partidos/", status_code=303)

@app.get("/partidos/{id}/delete")
async def delete_partido(id: int):
    partidos = load_partidos()
    partido = next((p for p in partidos if p.id == id), None)
    if partido:
        partidos = [p for p in partidos if p.id != id]
        update_csv(partidos, PARTIDOS_CSV, partido)
    return RedirectResponse(url="/partidos/", status_code=303)

# Rutas para Plantillas
@app.get("/plantillas/", response_class=HTMLResponse)
async def get_plantillas(request: Request):
    plantillas = load_plantillas()
    return templates.TemplateResponse("plantillas.html", {"request": request, "plantillas": plantillas})

@app.get("/plantillas/crear/", response_class=HTMLResponse)
async def create_plantilla_form(request: Request):
    return templates.TemplateResponse("plantillas_crear.html", {"request": request})

@app.post("/plantillas/crear/")
async def create_plantilla(
    equipo_id: int = Form(...),
    jugador_id: int = Form(...)
):
    plantillas = load_plantillas()
    new_id = max([p.id for p in plantillas] + [0]) + 1
    new_plantilla = Plantilla(
        id=new_id,
        equipo_id=equipo_id,
        jugador_id=jugador_id
    )
    update_csv(plantillas, PLANTILLA_CSV, new_plantilla)
    return RedirectResponse(url="/plantillas/", status_code=303)

@app.get("/plantillas/{id}/edit", response_class=HTMLResponse)
async def edit_plantilla_form(request: Request, id: int):
    plantillas = load_plantillas()
    plantilla = next((p for p in plantillas if p.id == id), None)
    if not plantilla:
        raise HTTPException(status_code=404, detail="Plantilla no encontrada")
    return templates.TemplateResponse("plantillas_edit.html", {"request": request, "plantilla": plantilla})

@app.post("/plantillas/{id}/update")
async def update_plantilla(
    id: int,
    equipo_id: int = Form(...),
    jugador_id: int = Form(...)
):
    plantillas = load_plantillas()
    plantilla = next((p for p in plantillas if p.id == id), None)
    if not plantilla:
        raise HTTPException(status_code=404, detail="Plantilla no encontrada")
    plantilla.equipo_id = equipo_id
    plantilla.jugador_id = jugador_id
    update_csv(plantillas, PLANTILLA_CSV, plantilla)
    return RedirectResponse(url="/plantillas/", status_code=303)

@app.get("/plantillas/{id}/delete")
async def delete_plantilla(id: int):
    plantillas = load_plantillas()
    plantilla = next((p for p in plantillas if p.id == id), None)
    if plantilla:
        plantillas = [p for p in plantillas if p.id != id]
        update_csv(plantillas, PLANTILLA_CSV, plantilla)
    return RedirectResponse(url="/plantillas/", status_code=303)

# Rutas para Torneos
@app.get("/torneos/", response_class=HTMLResponse)
async def get_torneos(request: Request):
    torneos = load_torneos()
    return templates.TemplateResponse("torneos.html", {"request": request, "torneos": torneos})

@app.get("/torneos/crear/", response_class=HTMLResponse)
async def create_torneo_form(request: Request):
    return templates.TemplateResponse("torneos_crear.html", {"request": request})

@app.post("/torneos/crear/")
async def create_torneo(
    nombre: str = Form(...),
    anio: int = Form(...),
    eliminado: str = Form(...)
):
    torneos = load_torneos()
    new_id = max([t.id for t in torneos] + [0]) + 1
    new_torneo = Torneo(
        id=new_id,
        nombre=nombre,
        anio=anio,
        eliminado=eliminado
    )
    update_csv(torneos, TORNEOS_CSV, new_torneo)
    return RedirectResponse(url="/torneos/", status_code=303)

@app.get("/torneos/{id}/edit", response_class=HTMLResponse)
async def edit_torneo_form(request: Request, id: int):
    torneos = load_torneos()
    torneo = next((t for t in torneos if t.id == id), None)
    if not torneo:
        raise HTTPException(status_code=404, detail="Torneo no encontrado")
    return templates.TemplateResponse("torneos_edit.html", {"request": request, "torneo": torneo})

@app.post("/torneos/{id}/update")
async def update_torneo(
    id: int,
    nombre: str = Form(...),
    anio: int = Form(...),
    eliminado: str = Form(...)
):
    torneos = load_torneos()
    torneo = next((t for t in torneos if t.id == id), None)
    if not torneo:
        raise HTTPException(status_code=404, detail="Torneo no encontrado")
    torneo.nombre = nombre
    torneo.anio = anio
    torneo.eliminado = eliminado
    update_csv(torneos, TORNEOS_CSV, torneo)
    return RedirectResponse(url="/torneos/", status_code=303)

@app.get("/torneos/{id}/delete")
async def delete_torneo(id: int):
    torneos = load_torneos()
    torneo = next((t for t in torneos if t.id == id), None)
    if torneo:
        torneos = [t for t in torneos if t.id != id]
        update_csv(torneos, TORNEOS_CSV, torneo)
    return RedirectResponse(url="/torneos/", status_code=303)

# Página principal
@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})