from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from typing import List, Optional
import pandas as pd
import csv
import os
from fastapi import HTTPException

app = FastAPI()
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

# Rutas de los archivos CSV
JUGADORES_CSV = "data/jugadores.csv"
EQUIPOS_CSV = "data/equipos.csv"
PARTIDOS_CSV = "data/partidos.csv"
PLANTILLA_CSV = "data/plantillas.csv"
TORNEOS_CSV = "data/torneos.csv"
PAPELERA_CSV = "data/trash.csv"

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
    imagen: Optional[str] = None

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
    torneo_id: Optional[int] = None
    eliminado: Optional[str] = None
    tarjetas_amarillas_local: int
    tarjetas_amarillas_visitante: int
    tarjetas_rojas_local: int
    tarjetas_rojas_visitante: int

class Plantilla(BaseModel):
    id: int
    equipo_id: int
    nombre: Optional[str] = None
    posicion: Optional[str] = None
    anio: Optional[int] = None
    torneo_id: Optional[int] = None
    jugador_id: Optional[int] = None

class Torneo(BaseModel):
    id: int
    nombre: str
    anio: int
    eliminado: str
    pais_anfitrion: Optional[str] = None
    estado: Optional[str] = None

class Papelera(BaseModel):
    id: int
    tipo: str
    data: dict

# Funciones de carga y actualización de datos
def load_csv(csv_file):
    if not os.path.exists(csv_file):
        return []
    df = pd.read_csv(csv_file)
    for column in df.columns:
        if column in ['imagen', 'pais_anfitrion', 'estado', 'torneo_id', 'eliminado']:
            df[column] = df[column].apply(lambda x: str(x).strip() if isinstance(x, str) and pd.notna(x) else None)
        elif df[column].dtype in ['float64', 'int64']:
            df[column] = df[column].apply(lambda x: 0 if pd.isna(x) else x)
    return df.to_dict(orient="records")

def update_csv(data_list, csv_file, new_item=None):
    data_dicts = [item.dict(exclude_unset=True) for item in data_list]
    if new_item:
        if isinstance(new_item, (Jugador, Equipo, Partido, Plantilla, Torneo)):
            data_dicts.append(new_item.dict(exclude_unset=True))
    fieldnames = list(dict.fromkeys([key for item in data_dicts for key in item.keys()]))
    with open(csv_file, mode='w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(data_dicts)
    return data_list

def load_papelera():
    if not os.path.exists(PAPELERA_CSV):
        return []
    df = pd.read_csv(PAPELERA_CSV, dtype=str)
    return [Papelera(id=int(item['id']), tipo=str(item['tipo']), data=eval(item['data'])) for item in df.to_dict(orient="records")]

def update_papelera(papelera_list, new_item=None):
    data_dicts = [{'id': item.id, 'tipo': item.tipo, 'data': str(item.data)} for item in papelera_list]
    if new_item:
        data_dicts.append({'id': new_item.id, 'tipo': new_item.tipo, 'data': str(new_item.data)})
    fieldnames = ['id', 'tipo', 'data']
    with open(PAPELERA_CSV, mode='w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(data_dicts)
    return papelera_list

def load_jugadores(): return [Jugador(**item) for item in load_csv(JUGADORES_CSV)]
def load_equipos(): return [Equipo(**item) for item in load_csv(EQUIPOS_CSV)]
def load_partidos(): return [Partido(**item) for item in load_csv(PARTIDOS_CSV)]
def load_plantillas(): return [Plantilla(**item) for item in load_csv(PLANTILLA_CSV)]
def load_torneos(): return [Torneo(**item) for item in load_csv(TORNEOS_CSV)]

# Rutas para Jugadores
@app.get("/jugadores/", response_class=HTMLResponse)
async def get_jugadores(request: Request):
    jugadores = load_jugadores()
    papelera = load_papelera()
    year = request.query_params.get("year")
    if year:
        jugadores = [j for j in jugadores if str(j.anio) == year]
    return templates.TemplateResponse("jugadores.html", {"request": request, "jugadores": jugadores, "papelera": papelera})

@app.get("/jugadores/crear/", response_class=HTMLResponse)
async def create_jugador_form(request: Request):
    return templates.TemplateResponse("jugadores_crear.html", {"request": request})

@app.post("/jugadores/crear/")
async def create_jugador(
    Jugadores: str = Form(...), F_Nacim_Edad: str = Form(...), Club: str = Form(...),
    Altura: str = Form(...), Pie: str = Form(...), Partidos_con_la_seleccion: int = Form(...),
    Goles: int = Form(...), Numero_de_camisa: int = Form(...), anio: int = Form(...),
    posicion: str = Form(...), activo: bool = Form(False), imagen: str = Form("")
):
    jugadores = load_jugadores()
    new_id = max([j.id for j in jugadores] + [0]) + 1
    new_jugador = Jugador(id=new_id, Jugadores=Jugadores, F_Nacim_Edad=F_Nacim_Edad, Club=Club,
                          Altura=Altura, Pie=Pie, Partidos_con_la_seleccion=Partidos_con_la_seleccion,
                          Goles=Goles, Numero_de_camisa=Numero_de_camisa, anio=anio, posicion=posicion,
                          activo=activo, imagen=imagen if imagen else None)
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
    id: int, Jugadores: str = Form(...), F_Nacim_Edad: str = Form(...), Club: str = Form(...),
    Altura: str = Form(...), Pie: str = Form(...), Partidos_con_la_seleccion: int = Form(...),
    Goles: int = Form(...), Numero_de_camisa: int = Form(...), anio: int = Form(...),
    posicion: str = Form(...), activo: bool = Form(False), imagen: str = Form("")
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
    update_csv(jugadores, JUGADORES_CSV)
    return RedirectResponse(url="/jugadores/", status_code=303)

@app.get("/jugadores/{id}/delete")
async def delete_jugador(id: int):
    jugadores = load_jugadores()
    jugador = next((j for j in jugadores if j.id == id), None)
    if jugador:
        jugadores = [j for j in jugadores if j.id != id]
        update_csv(jugadores, JUGADORES_CSV)
        papelera = load_papelera()
        papelera_item = Papelera(id=jugador.id, tipo="jugador", data=jugador.dict())
        update_papelera(papelera, papelera_item)
    return RedirectResponse(url="/jugadores/", status_code=303)

@app.get("/jugadores/{id}", response_class=HTMLResponse)
async def get_jugador_detalle(request: Request, id: int):
    jugadores = load_jugadores()
    jugador = next((j for j in jugadores if j.id == id), None)
    if not jugador:
        raise HTTPException(status_code=404, detail="Jugador no encontrado")
    return templates.TemplateResponse("jugadores_detalle.html", {"request": request, "jugador": jugador})

# Rutas para Equipos
@app.get("/equipos/", response_class=HTMLResponse)
async def get_equipos(request: Request):
    equipos = load_equipos()
    papelera = load_papelera()
    year = request.query_params.get("year")
    if year:
        equipos = [e for e in equipos if str(e.id)[:4] == year]
    return templates.TemplateResponse("equipos.html", {"request": request, "equipos": equipos, "papelera": papelera})

@app.get("/equipos/crear/", response_class=HTMLResponse)
async def create_equipo_form(request: Request):
    return templates.TemplateResponse("equipos_crear.html", {"request": request})

@app.post("/equipos/crear/")
async def create_equipo(nombre: str = Form(...), pais: str = Form(...), enfrentamientos_con_colombia: int = Form(...)):
    equipos = load_equipos()
    new_id = max([e.id for e in equipos] + [0]) + 1
    new_equipo = Equipo(id=new_id, nombre=nombre, pais=pais, enfrentamientos_con_colombia=enfrentamientos_con_colombia)
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
async def update_equipo(id: int, nombre: str = Form(...), pais: str = Form(...), enfrentamientos_con_colombia: int = Form(...)):
    equipos = load_equipos()
    equipo = next((e for e in equipos if e.id == id), None)
    if not equipo:
        raise HTTPException(status_code=404, detail="Equipo no encontrado")
    equipo.nombre = nombre
    equipo.pais = pais
    equipo.enfrentamientos_con_colombia = enfrentamientos_con_colombia
    update_csv(equipos, EQUIPOS_CSV)
    return RedirectResponse(url="/equipos/", status_code=303)

@app.get("/equipos/{id}/delete")
async def delete_equipo(id: int):
    equipos = load_equipos()
    equipo = next((e for e in equipos if e.id == id), None)
    if equipo:
        equipos = [e for e in equipos if e.id != id]
        update_csv(equipos, EQUIPOS_CSV)
        papelera = load_papelera()
        papelera_item = Papelera(id=equipo.id, tipo="equipo", data=equipo.dict())
        update_papelera(papelera, papelera_item)
    return RedirectResponse(url="/equipos/", status_code=303)

# Rutas para Partidos
@app.get("/partidos/", response_class=HTMLResponse)
async def get_partidos(request: Request):
    partidos = load_partidos()
    papelera = load_papelera()
    year = request.query_params.get("year")
    if year:
        partidos = [p for p in partidos if p.fecha and p.fecha.split('-')[0] == year]
    return templates.TemplateResponse("partidos.html", {"request": request, "partidos": partidos, "papelera": papelera})

@app.get("/partidos/crear/", response_class=HTMLResponse)
async def create_partido_form(request: Request):
    torneos = load_torneos()
    return templates.TemplateResponse("partidos_crear.html", {"request": request, "torneos": torneos})

@app.post("/partidos/crear/")
async def create_partido(
    fecha: str = Form(...), equipo_local: str = Form(...), equipo_visitante: str = Form(...),
    goles_local: int = Form(...), goles_visitante: int = Form(...), torneo_id: Optional[int] = Form(None),
    eliminado: str = Form(""), tarjetas_amarillas_local: int = Form(0), tarjetas_amarillas_visitante: int = Form(0),
    tarjetas_rojas_local: int = Form(0), tarjetas_rojas_visitante: int = Form(0)
):
    partidos = load_partidos()
    new_id = max([p.id for p in partidos] + [0]) + 1
    new_partido = Partido(id=new_id, fecha=fecha, equipo_local=equipo_local, equipo_visitante=equipo_visitante,
                          goles_local=goles_local, goles_visitante=goles_visitante, torneo_id=torneo_id,
                          eliminado=eliminado if eliminado else None, tarjetas_amarillas_local=tarjetas_amarillas_local,
                          tarjetas_amarillas_visitante=tarjetas_amarillas_visitante,
                          tarjetas_rojas_local=tarjetas_rojas_local, tarjetas_rojas_visitante=tarjetas_rojas_visitante)
    update_csv(partidos, PARTIDOS_CSV, new_partido)
    return RedirectResponse(url="/partidos/", status_code=303)

@app.get("/partidos/{id}/edit", response_class=HTMLResponse)
async def edit_partido_form(request: Request, id: int):
    partidos = load_partidos()
    partido = next((p for p in partidos if p.id == id), None)
    torneos = load_torneos()
    if not partido:
        raise HTTPException(status_code=404, detail="Partido no encontrado")
    return templates.TemplateResponse("partidos_edit.html", {"request": request, "partido": partido, "torneos": torneos})

@app.post("/partidos/{id}/update")
async def update_partido(
    id: int, fecha: str = Form(...), equipo_local: str = Form(...), equipo_visitante: str = Form(...),
    goles_local: int = Form(...), goles_visitante: int = Form(...), torneo_id: Optional[int] = Form(None),
    eliminado: str = Form(""), tarjetas_amarillas_local: int = Form(0), tarjetas_amarillas_visitante: int = Form(0),
    tarjetas_rojas_local: int = Form(0), tarjetas_rojas_visitante: int = Form(0)
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
    partido.eliminado = eliminado if eliminado else None
    partido.tarjetas_amarillas_local = tarjetas_amarillas_local
    partido.tarjetas_amarillas_visitante = tarjetas_amarillas_visitante
    partido.tarjetas_rojas_local = tarjetas_rojas_local
    partido.tarjetas_rojas_visitante = tarjetas_rojas_visitante
    update_csv(partidos, PARTIDOS_CSV)
    return RedirectResponse(url="/partidos/", status_code=303)

@app.get("/partidos/{id}/delete")
async def delete_partido(id: int):
    partidos = load_partidos()
    partido = next((p for p in partidos if p.id == id), None)
    if partido:
        partidos = [p for p in partidos if p.id != id]
        update_csv(partidos, PARTIDOS_CSV)
        papelera = load_papelera()
        papelera_item = Papelera(id=partido.id, tipo="partido", data=partido.dict())
        update_papelera(papelera, papelera_item)
    return RedirectResponse(url="/partidos/", status_code=303)

# Rutas para Plantillas
@app.get("/plantillas/", response_class=HTMLResponse)
async def get_plantillas(request: Request):
    plantillas = load_plantillas()
    papelera = load_papelera()
    jugadores = load_jugadores()
    equipos = load_equipos()
    torneos = load_torneos()
    year = request.query_params.get("year")
    if year:
        plantillas = [p for p in plantillas if str(p.anio) == year]
    return templates.TemplateResponse("plantillas.html", {"request": request, "plantillas": plantillas, "jugadores": jugadores, "equipos": equipos, "torneos": torneos, "papelera": papelera})

@app.get("/plantillas/crear/", response_class=HTMLResponse)
async def create_plantilla_form(request: Request):
    equipos = load_equipos()
    jugadores = load_jugadores()
    torneos = load_torneos()
    return templates.TemplateResponse("plantillas_crear.html", {"request": request, "equipos": equipos, "jugadores": jugadores, "torneos": torneos})

@app.post("/plantillas/crear/")
async def create_plantilla(
    equipo_id: int = Form(...), nombre: str = Form(...), posicion: str = Form(...), anio: int = Form(...), torneo_id: int = Form(...), jugador_id: int = Form(...)
):
    plantillas = load_plantillas()
    new_id = max([p.id for p in plantillas] + [0]) + 1
    new_plantilla = Plantilla(id=new_id, equipo_id=equipo_id, nombre=nombre, posicion=posicion, anio=anio, torneo_id=torneo_id, jugador_id=jugador_id)
    update_csv(plantillas, PLANTILLA_CSV, new_plantilla)
    return RedirectResponse(url="/plantillas/", status_code=303)

@app.get("/plantillas/{id}/edit", response_class=HTMLResponse)
async def edit_plantilla_form(request: Request, id: int):
    plantillas = load_plantillas()
    plantilla = next((p for p in plantillas if p.id == id), None)
    equipos = load_equipos()
    jugadores = load_jugadores()
    torneos = load_torneos()
    if not plantilla:
        raise HTTPException(status_code=404, detail="Plantilla no encontrada")
    return templates.TemplateResponse("plantillas_edit.html", {"request": request, "plantilla": plantilla, "equipos": equipos, "jugadores": jugadores, "torneos": torneos})

@app.post("/plantillas/{id}/update")
async def update_plantilla(
    id: int, equipo_id: int = Form(...), nombre: str = Form(...), posicion: str = Form(...), anio: int = Form(...), torneo_id: int = Form(...), jugador_id: int = Form(...)
):
    plantillas = load_plantillas()
    plantilla = next((p for p in plantillas if p.id == id), None)
    if not plantilla:
        raise HTTPException(status_code=404, detail="Plantilla no encontrada")
    plantilla.equipo_id = equipo_id
    plantilla.nombre = nombre
    plantilla.posicion = posicion
    plantilla.anio = anio
    plantilla.torneo_id = torneo_id
    plantilla.jugador_id = jugador_id
    update_csv(plantillas, PLANTILLA_CSV)
    return RedirectResponse(url="/plantillas/", status_code=303)

@app.get("/plantillas/{id}/delete")
async def delete_plantilla(id: int):
    plantillas = load_plantillas()
    plantilla = next((p for p in plantillas if p.id == id), None)
    if plantilla:
        plantillas = [p for p in plantillas if p.id != id]
        update_csv(plantillas, PLANTILLA_CSV)
        papelera = load_papelera()
        papelera_item = Papelera(id=plantilla.id, tipo="plantilla", data=plantilla.dict())
        update_papelera(papelera, papelera_item)
    return RedirectResponse(url="/plantillas/", status_code=303)

# Rutas para Torneos
@app.get("/torneos/", response_class=HTMLResponse)
async def get_torneos(request: Request):
    torneos = load_torneos()
    papelera = load_papelera()
    year = request.query_params.get("year")
    if year:
        torneos = [t for t in torneos if str(t.anio) == year]
    return templates.TemplateResponse("torneos.html", {"request": request, "torneos": torneos, "papelera": papelera})

@app.get("/torneos/crear/", response_class=HTMLResponse)
async def create_torneo_form(request: Request):
    return templates.TemplateResponse("torneos_crear.html", {"request": request})

@app.post("/torneos/crear/")
async def create_torneo(nombre: str = Form(...), anio: int = Form(...), eliminado: str = Form(...),
                       pais_anfitrion: str = Form(""), estado: str = Form("")):
    torneos = load_torneos()
    new_id = max([t.id for t in torneos] + [0]) + 1
    new_torneo = Torneo(id=new_id, nombre=nombre, anio=anio, eliminado=eliminado,
                        pais_anfitrion=pais_anfitrion if pais_anfitrion else None,
                        estado=estado if estado else None)
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
async def update_torneo(id: int, nombre: str = Form(...), anio: int = Form(...), eliminado: str = Form(...),
                       pais_anfitrion: str = Form(""), estado: str = Form("")):
    torneos = load_torneos()
    torneo = next((t for t in torneos if t.id == id), None)
    if not torneo:
        raise HTTPException(status_code=404, detail="Torneo no encontrado")
    torneo.nombre = nombre
    torneo.anio = anio
    torneo.eliminado = eliminado
    torneo.pais_anfitrion = pais_anfitrion if pais_anfitrion else None
    torneo.estado = estado if estado else None
    update_csv(torneos, TORNEOS_CSV)
    return RedirectResponse(url="/torneos/", status_code=303)

@app.get("/torneos/{id}/delete")
async def delete_torneo(id: int):
    torneos = load_torneos()
    torneo = next((t for t in torneos if t.id == id), None)
    if torneo:
        torneos = [t for t in torneos if t.id != id]
        update_csv(torneos, TORNEOS_CSV)
        papelera = load_papelera()
        papelera_item = Papelera(id=torneo.id, tipo="torneo", data=torneo.dict())
        update_papelera(papelera, papelera_item)
    return RedirectResponse(url="/torneos/", status_code=303)

# Rutas para Estadísticas
@app.get("/estadisticas/completa/", response_class=HTMLResponse)
async def get_estadisticas_completa(request: Request):
    jugadores = load_jugadores()
    partidos = load_partidos()
    torneos = load_torneos()

    victorias_total = 0
    goles_total = 0
    partidos_jugados_total = 0
    victorias_por_anio = {}
    goles_por_anio = {}
    partidos_jugados_por_anio = {}

    for p in partidos:
        try:
            anio = p.fecha.split('-')[0] if p.fecha and '-' in p.fecha else "0"
            if p.equipo_local == "Colombia" or p.equipo_visitante == "Colombia":
                partidos_jugados_total += 1
                partidos_jugados_por_anio[anio] = partidos_jugados_por_anio.get(anio, 0) + 1
                goles_total += (p.goles_local if p.equipo_local == "Colombia" else 0) + (p.goles_visitante if p.equipo_visitante == "Colombia" else 0)
                goles_por_anio[anio] = goles_por_anio.get(anio, 0) + (p.goles_local if p.equipo_local == "Colombia" else 0) + (p.goles_visitante if p.equipo_visitante == "Colombia" else 0)
                if (p.equipo_local == "Colombia" and p.goles_local > p.goles_visitante) or (p.equipo_visitante == "Colombia" and p.goles_visitante > p.goles_local):
                    victorias_total += 1
                    victorias_por_anio[anio] = victorias_por_anio.get(anio, 0) + 1
        except (IndexError, AttributeError):
            continue

    promedio_goles_total = goles_total / partidos_jugados_total if partidos_jugados_total > 0 else 0
    promedio_goles_por_anio = {anio: goles / partidos for anio, goles in goles_por_anio.items() for partidos in [partidos_jugados_por_anio.get(anio, 1)] if partidos_jugados_por_anio.get(anio, 1) > 0}

    return templates.TemplateResponse("estadisticas_completa.html", {
        "request": request, "jugadores": jugadores, "partidos": partidos, "torneos": torneos,
        "victorias_total": victorias_total, "goles_total": goles_total, "partidos_jugados_total": partidos_jugados_total,
        "promedio_goles_total": promedio_goles_total, "victorias_por_anio": victorias_por_anio,
        "goles_por_anio": goles_por_anio, "partidos_jugados_por_anio": partidos_jugados_por_anio,
        "promedio_goles_por_anio": promedio_goles_por_anio
    })

# Página principal y documentación
@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.get("/documentacion/", response_class=HTMLResponse)
async def get_documentacion(request: Request):
    return templates.TemplateResponse("documentacion.html", {"request": request})