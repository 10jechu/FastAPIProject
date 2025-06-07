from fastapi import FastAPI, Request, Form, HTTPException, File, UploadFile
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import ValidationError
import pandas as pd
import os
import shutil
from modelos.jugador import Jugador
from modelos.equipo import Equipo
from modelos.partido import Partido
from modelos.torneo import Torneo
from modelos.plantilla import Plantilla
from datetime import date

app = FastAPI(
    title="Gestión Selección Colombia",
    description="Aplicación para gestionar jugadores, equipos, partidos, torneos y plantillas de la Selección Colombia.",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Montar archivos estáticos
app.mount("/static", StaticFiles(directory="static"), name="static")

# Configurar Jinja2 para las plantillas
templates = Jinja2Templates(directory="templates")

# Directorio de datos
DATA_DIR = "data"
IMAGES_DIR = os.path.join("static", "images")
os.makedirs(DATA_DIR, exist_ok=True)
os.makedirs(IMAGES_DIR, exist_ok=True)
JUGADORES_CSV = os.path.join(DATA_DIR, "jugadores.csv")
EQUIPOS_CSV = os.path.join(DATA_DIR, "equipos.csv")
PARTIDOS_CSV = os.path.join(DATA_DIR, "partidos.csv")
TORNEOS_CSV = os.path.join(DATA_DIR, "torneos.csv")
PLANTILLAS_CSV = os.path.join(DATA_DIR, "plantillas.csv")

# Funciones auxiliares para manejar CSV
def load_csv(file_path):
    try:
        df = pd.read_csv(file_path)
        return df.to_dict('records')
    except FileNotFoundError:
        return []
    except pd.errors.EmptyDataError:
        return []

def save_csv(file_path, data):
    df = pd.DataFrame(data)
    df.to_csv(file_path, index=False)

# --- Jugadores ---
def load_jugadores():
    return load_csv(JUGADORES_CSV)

def save_jugadores(jugadores):
    save_csv(JUGADORES_CSV, jugadores)

@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
    jugadores = load_jugadores()
    return templates.TemplateResponse(
        "index.html",
        {"request": request, "jugadores": jugadores}
    )

@app.get("/jugadores/", response_class=HTMLResponse)
async def get_jugadores(request: Request):
    jugadores = load_jugadores()
    return templates.TemplateResponse(
        "jugadores.html",
        {"request": request, "jugadores": jugadores}
    )

@app.get("/jugadores/crear/", response_class=HTMLResponse)
async def create_jugador_form(request: Request):
    return templates.TemplateResponse("jugadores_crear.html", {"request": request})

@app.post("/jugadores/")
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
    posicion: str = Form(None),
    activo: bool = Form(True),
    imagen: UploadFile = File(None)
):
    try:
        jugadores = load_jugadores()
        new_id = max([j['id'] for j in jugadores], default=0) + 1
        imagen_filename = None
        if imagen:
            imagen_filename = f"jugador_{new_id}.{imagen.filename.split('.')[-1]}"
            with open(os.path.join(IMAGES_DIR, imagen_filename), "wb") as buffer:
                shutil.copyfileobj(imagen.file, buffer)
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
            imagen=imagen_filename
        )
        jugadores.append(new_jugador.dict())
        save_jugadores(jugadores)
        return RedirectResponse(url="/jugadores/", status_code=303)
    except ValidationError as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/jugadores/{id}", response_class=HTMLResponse)
async def get_jugador(request: Request, id: int):
    jugadores = load_jugadores()
    jugador = next((j for j in jugadores if j['id'] == id), None)
    if not jugador:
        raise HTTPException(status_code=404, detail="Jugador no encontrado")
    return templates.TemplateResponse(
        "jugador_detail.html",
        {"request": request, "jugador": jugador}
    )

@app.get("/jugadores/{id}/edit", response_class=HTMLResponse)
async def edit_jugador_form(request: Request, id: int):
    jugadores = load_jugadores()
    jugador = next((j for j in jugadores if j['id'] == id), None)
    if not jugador:
        raise HTTPException(status_code=404, detail="Jugador no encontrado")
    return templates.TemplateResponse(
        "jugadores_edit.html",
        {"request": request, "jugador": jugador}
    )

@app.post("/jugadores/{id}/")
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
    posicion: str = Form(None),
    activo: bool = Form(True),
    imagen: UploadFile = File(None),
    method: str = Form(None)
):
    jugadores = load_jugadores()
    if method == "DELETE":
        jugadores = [j for j in jugadores if j['id'] != id]
        save_jugadores(jugadores)
        return RedirectResponse(url="/jugadores/", status_code=303)
    else:
        imagen_filename = None
        for j in jugadores:
            if j['id'] == id:
                imagen_filename = j.get('imagen')
                break
        if imagen:
            imagen_filename = f"jugador_{id}.{imagen.filename.split('.')[-1]}"
            with open(os.path.join(IMAGES_DIR, imagen_filename), "wb") as buffer:
                shutil.copyfileobj(imagen.file, buffer)
        updated_jugador = Jugador(
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
            activo=activo,
            imagen=imagen_filename
        )
        jugadores = [updated_jugador.dict() if j['id'] == id else j for j in jugadores]
        save_jugadores(jugadores)
        return RedirectResponse(url=f"/jugadores/{id}", status_code=303)

# --- Equipos ---
def load_equipos():
    return load_csv(EQUIPOS_CSV)

def save_equipos(equipos):
    save_csv(EQUIPOS_CSV, equipos)

@app.get("/equipos/", response_class=HTMLResponse)
async def get_equipos(request: Request):
    equipos = load_equipos()
    return templates.TemplateResponse(
        "equipos.html",
        {"request": request, "equipos": equipos}
    )

@app.get("/equipos/crear/", response_class=HTMLResponse)
async def create_equipo_form(request: Request):
    return templates.TemplateResponse("equipos_crear.html", {"request": request})

@app.post("/equipos/")
async def create_equipo(
    nombre: str = Form(...),
    pais: str = Form(...),
    enfrentamientos: int = Form(...)
):
    try:
        equipos = load_equipos()
        new_id = max([e['id'] for e in equipos], default=0) + 1
        new_equipo = Equipo(
            id=new_id,
            nombre=nombre,
            pais=pais,
            enfrentamientos=enfrentamientos
        )
        equipos.append(new_equipo.dict())
        save_equipos(equipos)
        return RedirectResponse(url="/equipos/", status_code=303)
    except ValidationError as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/equipos/{id}", response_class=HTMLResponse)
async def get_equipo(request: Request, id: int):
    equipos = load_equipos()
    equipo = next((e for e in equipos if e['id'] == id), None)
    if not equipo:
        raise HTTPException(status_code=404, detail="Equipo no encontrado")
    return templates.TemplateResponse(
        "equipo_detail.html",
        {"request": request, "equipo": equipo}
    )

@app.get("/equipos/{id}/edit", response_class=HTMLResponse)
async def edit_equipo_form(request: Request, id: int):
    equipos = load_equipos()
    equipo = next((e for e in equipos if e['id'] == id), None)
    if not equipo:
        raise HTTPException(status_code=404, detail="Equipo no encontrado")
    return templates.TemplateResponse(
        "equipos_edit.html",
        {"request": request, "equipo": equipo}
    )

@app.post("/equipos/{id}/")
async def update_equipo(
    id: int,
    nombre: str = Form(...),
    pais: str = Form(...),
    enfrentamientos: int = Form(...),
    method: str = Form(None)
):
    equipos = load_equipos()
    if method == "DELETE":
        equipos = [e for e in equipos if e['id'] != id]
        save_equipos(equipos)
        return RedirectResponse(url="/equipos/", status_code=303)
    else:
        updated_equipo = Equipo(
            id=id,
            nombre=nombre,
            pais=pais,
            enfrentamientos=enfrentamientos
        )
        equipos = [updated_equipo.dict() if e['id'] == id else e for e in equipos]
        save_equipos(equipos)
        return RedirectResponse(url=f"/equipos/{id}", status_code=303)

# --- Partidos ---
def load_partidos():
    return load_csv(PARTIDOS_CSV)

def save_partidos(partidos):
    save_csv(PARTIDOS_CSV, partidos)

@app.get("/partidos/", response_class=HTMLResponse)
async def get_partidos(request: Request):
    partidos = load_partidos()
    return templates.TemplateResponse(
        "partidos.html",
        {"request": request, "partidos": partidos}
    )

@app.get("/partidos/crear/", response_class=HTMLResponse)
async def create_partido_form(request: Request):
    equipos = load_equipos()
    torneos = load_torneos()
    return templates.TemplateResponse(
        "partidos_crear.html",
        {"request": request, "equipos": equipos, "torneos": torneos}
    )

@app.post("/partidos/")
async def create_partido(
    equipo_local: str = Form(...),
    equipo_visitante: str = Form(...),
    fecha: str = Form(...),
    goles_local: int = Form(...),
    goles_visitante: int = Form(...),
    torneo_id: int = Form(...),
    eliminado: str = Form(...),
    tarjetas_amarillas_local: int = Form(...),
    tarjetas_amarillas_visitante: int = Form(...),
    tarjetas_rojas_local: int = Form(...),
    tarjetas_rojas_visitante: int = Form(...)
):
    try:
        partidos = load_partidos()
        new_id = max([p['id'] for p in partidos], default=0) + 1
        new_partido = Partido(
            id=new_id,
            equipo_local=equipo_local,
            equipo_visitante=equipo_visitante,
            fecha=fecha,
            goles_local=goles_local,
            goles_visitante=goles_visitante,
            torneo_id=torneo_id,
            eliminado=eliminado,
            tarjetas_amarillas_local=tarjetas_amarillas_local,
            tarjetas_amarillas_visitante=tarjetas_amarillas_visitante,
            tarjetas_rojas_local=tarjetas_rojas_local,
            tarjetas_rojas_visitante=tarjetas_rojas_visitante
        )
        partidos.append(new_partido.dict())
        save_partidos(partidos)
        return RedirectResponse(url="/partidos/", status_code=303)
    except ValidationError as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/partidos/{id}", response_class=HTMLResponse)
async def get_partido(request: Request, id: int):
    partidos = load_partidos()
    partido = next((p for p in partidos if p['id'] == id), None)
    if not partido:
        raise HTTPException(status_code=404, detail="Partido no encontrado")
    return templates.TemplateResponse(
        "partido_detail.html",
        {"request": request, "partido": partido}
    )

@app.get("/partidos/{id}/edit", response_class=HTMLResponse)
async def edit_partido_form(request: Request, id: int):
    partidos = load_partidos()
    partido = next((p for p in partidos if p['id'] == id), None)
    if not partido:
        raise HTTPException(status_code=404, detail="Partido no encontrado")
    equipos = load_equipos()
    torneos = load_torneos()
    return templates.TemplateResponse(
        "partidos_edit.html",
        {"request": request, "partido": partido, "equipos": equipos, "torneos": torneos}
    )

@app.post("/partidos/{id}/")
async def update_partido(
    id: int,
    equipo_local: str = Form(...),
    equipo_visitante: str = Form(...),
    fecha: str = Form(...),
    goles_local: int = Form(...),
    goles_visitante: int = Form(...),
    torneo_id: int = Form(...),
    eliminado: str = Form(...),
    tarjetas_amarillas_local: int = Form(...),
    tarjetas_amarillas_visitante: int = Form(...),
    tarjetas_rojas_local: int = Form(...),
    tarjetas_rojas_visitante: int = Form(...),
    method: str = Form(None)
):
    partidos = load_partidos()
    if method == "DELETE":
        partidos = [p for p in partidos if p['id'] != id]
        save_partidos(partidos)
        return RedirectResponse(url="/partidos/", status_code=303)
    else:
        updated_partido = Partido(
            id=id,
            equipo_local=equipo_local,
            equipo_visitante=equipo_visitante,
            fecha=fecha,
            goles_local=goles_local,
            goles_visitante=goles_visitante,
            torneo_id=torneo_id,
            eliminado=eliminado,
            tarjetas_amarillas_local=tarjetas_amarillas_local,
            tarjetas_amarillas_visitante=tarjetas_amarillas_visitante,
            tarjetas_rojas_local=tarjetas_rojas_local,
            tarjetas_rojas_visitante=tarjetas_rojas_visitante
        )
        partidos = [updated_partido.dict() if p['id'] == id else p for p in partidos]
        save_partidos(partidos)
        return RedirectResponse(url=f"/partidos/{id}", status_code=303)

# --- Torneos ---
def load_torneos():
    return load_csv(TORNEOS_CSV)

def save_torneos(torneos):
    save_csv(TORNEOS_CSV, torneos)

@app.get("/torneos/", response_class=HTMLResponse)
async def get_torneos(request: Request):
    torneos = load_torneos()
    return templates.TemplateResponse(
        "torneos.html",
        {"request": request, "torneos": torneos}
    )

@app.get("/torneos/crear/", response_class=HTMLResponse)
async def create_torneo_form(request: Request):
    return templates.TemplateResponse("torneos_crear.html", {"request": request})

@app.post("/torneos/")
async def create_torneo(
    nombre: str = Form(...),
    anio: int = Form(...),
    pais_anfitrion: str = Form(None),
    estado: str = Form(...),
    eliminado: str = Form(...)
):
    try:
        torneos = load_torneos()
        new_id = max([t['id'] for t in torneos], default=0) + 1
        new_torneo = Torneo(
            id=new_id,
            nombre=nombre,
            anio=anio,
            pais_anfitrion=pais_anfitrion,
            estado=estado,
            eliminado=eliminado
        )
        torneos.append(new_torneo.dict())
        save_torneos(torneos)
        return RedirectResponse(url="/torneos/", status_code=303)
    except ValidationError as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/torneos/{id}", response_class=HTMLResponse)
async def get_torneo(request: Request, id: int):
    torneos = load_torneos()
    torneo = next((t for t in torneos if t['id'] == id), None)
    if not torneo:
        raise HTTPException(status_code=404, detail="Torneo no encontrado")
    return templates.TemplateResponse(
        "torneo_detail.html",
        {"request": request, "torneo": torneo}
    )

@app.get("/torneos/{id}/edit", response_class=HTMLResponse)
async def edit_torneo_form(request: Request, id: int):
    torneos = load_torneos()
    torneo = next((t for t in torneos if t['id'] == id), None)
    if not torneo:
        raise HTTPException(status_code=404, detail="Torneo no encontrado")
    return templates.TemplateResponse(
        "torneos_edit.html",
        {"request": request, "torneo": torneo}
    )

@app.post("/torneos/{id}/")
async def update_torneo(
    id: int,
    nombre: str = Form(...),
    anio: int = Form(...),
    pais_anfitrion: str = Form(None),
    estado: str = Form(...),
    eliminado: str = Form(...),
    method: str = Form(None)
):
    torneos = load_torneos()
    if method == "DELETE":
        torneos = [t for t in torneos if t['id'] != id]
        save_torneos(torneos)
        return RedirectResponse(url="/torneos/", status_code=303)
    else:
        updated_torneo = Torneo(
            id=id,
            nombre=nombre,
            anio=anio,
            pais_anfitrion=pais_anfitrion,
            estado=estado,
            eliminado=eliminado
        )
        torneos = [updated_torneo.dict() if t['id'] == id else t for t in torneos]
        save_torneos(torneos)
        return RedirectResponse(url=f"/torneos/{id}", status_code=303)

# --- Plantillas ---
def load_plantillas():
    return load_csv(PLANTILLAS_CSV)

def save_plantillas(plantillas):
    save_csv(PLANTILLAS_CSV, plantillas)

@app.get("/plantillas/", response_class=HTMLResponse)
async def get_plantillas(request: Request):
    plantillas = load_plantillas()
    return templates.TemplateResponse(
        "plantillas.html",
        {"request": request, "plantillas": plantillas}
    )

@app.get("/plantillas/crear/", response_class=HTMLResponse)
async def create_plantilla_form(request: Request):
    equipos = load_equipos()
    torneos = load_torneos()
    jugadores = load_jugadores()
    return templates.TemplateResponse(
        "plantillas_crear.html",
        {"request": request, "equipos": equipos, "torneos": torneos, "jugadores": jugadores}
    )

@app.post("/plantillas/")
async def create_plantilla(
    equipo_id: int = Form(...),
    nombre: str = Form(None),
    posicion: str = Form(None),
    anio: int = Form(...),
    torneo_id: int = Form(None),
    jugador_id: int = Form(None)
):
    try:
        plantillas = load_plantillas()
        new_id = max([p['id'] for p in plantillas], default=0) + 1
        new_plantilla = Plantilla(
            id=new_id,
            equipo_id=equipo_id,
            nombre=nombre,
            posicion=posicion,
            anio=anio,
            torneo_id=torneo_id,
            jugador_id=jugador_id
        )
        plantillas.append(new_plantilla.dict())
        save_plantillas(plantillas)
        return RedirectResponse(url="/plantillas/", status_code=303)
    except ValidationError as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/plantillas/{id}", response_class=HTMLResponse)
async def get_plantilla(request: Request, id: int):
    plantillas = load_plantillas()
    plantilla = next((p for p in plantillas if p['id'] == id), None)
    if not plantilla:
        raise HTTPException(status_code=404, detail="Plantilla no encontrada")
    return templates.TemplateResponse(
        "plantilla_detail.html",
        {"request": request, "plantilla": plantilla}
    )

@app.get("/plantillas/{id}/edit", response_class=HTMLResponse)
async def edit_plantilla_form(request: Request, id: int):
    plantillas = load_plantillas()
    plantilla = next((p for p in plantillas if p['id'] == id), None)
    if not plantilla:
        raise HTTPException(status_code=404, detail="Plantilla no encontrada")
    equipos = load_equipos()
    torneos = load_torneos()
    jugadores = load_jugadores()
    return templates.TemplateResponse(
        "plantillas_edit.html",
        {"request": request, "plantilla": plantilla, "equipos": equipos, "torneos": torneos, "jugadores": jugadores}
    )

@app.post("/plantillas/{id}/")
async def update_plantilla(
    id: int,
    equipo_id: int = Form(...),
    nombre: str = Form(None),
    posicion: str = Form(None),
    anio: int = Form(...),
    torneo_id: int = Form(None),
    jugador_id: int = Form(None),
    method: str = Form(None)
):
    plantillas = load_plantillas()
    if method == "DELETE":
        plantillas = [p for p in plantillas if p['id'] != id]
        save_plantillas(plantillas)
        return RedirectResponse(url="/plantillas/", status_code=303)
    else:
        updated_plantilla = Plantilla(
            id=id,
            equipo_id=equipo_id,
            nombre=nombre,
            posicion=posicion,
            anio=anio,
            torneo_id=torneo_id,
            jugador_id=jugador_id
        )
        plantillas = [updated_plantilla.dict() if p['id'] == id else p for p in plantillas]
        save_plantillas(plantillas)
        return RedirectResponse(url=f"/plantillas/{id}", status_code=303)

# --- Estadísticas ---
@app.get("/estadisticas/", response_class=HTMLResponse)
async def get_estadisticas(request: Request):
    jugadores = load_jugadores()
    partidos = load_partidos()
    total_jugadores = len(jugadores)
    promedio_goles = round(sum(j['Goles'] for j in jugadores) / total_jugadores, 2) if total_jugadores > 0 else 0
    promedio_partidos = round(sum(j['Partidos_con_la_seleccion'] for j in jugadores) / total_jugadores, 2) if total_jugadores > 0 else 0
    total_partidos = len(partidos)
    victorias_colombia = sum(1 for p in partidos if (p['equipo_local'] == 'Colombia' and p['goles_local'] > p['goles_visitante']) or (p['equipo_visitante'] == 'Colombia' and p['goles_visitante'] > p['goles_local']))

    posiciones = {}
    for j in jugadores:
        pos = j['posicion'] or 'Desconocida'
        posiciones[pos] = posiciones.get(pos, 0) + 1

    chart_config = {
        "type": "bar",
        "data": {
            "labels": ["Arquero", "Defensa", "Mediocampista", "Delantero"],
            "datasets": [{
                "label": "Jugadores por Posición",
                "data": [
                    posiciones.get('Arquero', 0),
                    posiciones.get('Defensa', 0),
                    posiciones.get('Mediocampista', 0),
                    posiciones.get('Delantero', 0)
                ],
                "backgroundColor": ["#003087", "#ffcc00", "#d32f2f", "#4caf50"],
                "borderColor": ["#000000"],
                "borderWidth": 1
            }]
        },
        "options": {
            "scales": {
                "y": {
                    "beginAtZero": True
                }
            }
        }
    }

    return templates.TemplateResponse(
        "estadisticas.html",
        {
            "request": request,
            "total_jugadores": total_jugadores,
            "promedio_goles": promedio_goles,
            "promedio_partidos": promedio_partidos,
            "total_partidos": total_partidos,
            "victorias_colombia": victorias_colombia,
            "chart_config": chart_config
        }
    )

# --- Documentación ---
@app.get("/documentacion/", response_class=HTMLResponse)
async def get_documentacion(request: Request):
    return templates.TemplateResponse("documentacion.html", {"request": request})

# --- Planeación ---
@app.get("/planeacion/", response_class=HTMLResponse)
async def get_planeacion(request: Request):
    return templates.TemplateResponse("planeacion.html", {"request": request})

# --- Diseño ---
@app.get("/diseno/", response_class=HTMLResponse)
async def get_diseno(request: Request):
    return templates.TemplateResponse("diseno.html", {"request": request})

# --- Objetivo ---
@app.get("/objetivo/", response_class=HTMLResponse)
async def get_objetivo(request: Request):
    return templates.TemplateResponse("objetivo.html", {"request": request})