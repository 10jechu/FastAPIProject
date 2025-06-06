from fastapi import FastAPI, Request, Form, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import os
from utils.csv_handler import CSVHandler
from utils.exceptions import NotFoundException
from equipo import Equipo
from jugador import Jugador
from partido import Partido
from plantilla import Plantilla
from torneo import Torneo
from datetime import date

app = FastAPI()

# Montar archivos estáticos
app.mount("/static", StaticFiles(directory="static"), name="static")

# Configurar Jinja2 para las plantillas
templates = Jinja2Templates(directory="templates")

# Inicializar handlers para cada CSV
DATA_DIR = "data"
os.makedirs(DATA_DIR, exist_ok=True)

JUGADORES_CSV = os.path.join(DATA_DIR, "jugadores.csv")
EQUIPOS_CSV = os.path.join(DATA_DIR, "equipos.csv")
PARTIDOS_CSV = os.path.join(DATA_DIR, "partidos.csv")
TORNEOS_CSV = os.path.join(DATA_DIR, "torneos.csv")
PLANTILLAS_CSV = os.path.join(DATA_DIR, "plantillas.csv")

jugadores_handler = CSVHandler(JUGADORES_CSV)
equipos_handler = CSVHandler(EQUIPOS_CSV)
partidos_handler = CSVHandler(PARTIDOS_CSV)
torneos_handler = CSVHandler(TORNEOS_CSV)
plantillas_handler = CSVHandler(PLANTILLAS_CSV)

# Rutas CRUD para Jugadores
@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
    jugadores = jugadores_handler.read_all(Jugador)
    equipos = equipos_handler.read_all(Equipo)
    partidos = partidos_handler.read_all(Partido)
    torneos = torneos_handler.read_all(Torneo)
    plantillas = plantillas_handler.read_all(Plantilla)
    return templates.TemplateResponse(
        "index.html",
        {"request": request, "jugadores": jugadores[:5], "equipos": equipos[:5], "partidos": partidos[:5], "torneos": torneos[:5], "plantillas": plantillas[:5]}
    )

@app.get("/jugadores/", response_class=HTMLResponse)
async def get_jugadores(request: Request):
    jugadores = jugadores_handler.read_all(Jugador)
    return templates.TemplateResponse("jugadores.html", {"request": request, "jugadores": jugadores})

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
    activo: bool = Form(True)
):
    jugadores = jugadores_handler.read_all(Jugador)
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
        activo=activo
    ).dict()
    jugadores.append(new_jugador)
    jugadores_handler.write_all(jugadores)
    return RedirectResponse(url=f"/jugadores/{new_id}", status_code=303)

@app.get("/jugadores/{id}", response_class=HTMLResponse)
async def get_jugador(request: Request, id: int):
    jugadores = jugadores_handler.read_all(Jugador)
    jugador = next((j for j in jugadores if j.id == id), None)
    if not jugador:
        raise NotFoundException("Jugador", str(id))
    return templates.TemplateResponse("jugador_detail.html", {"request": request, "jugador": jugador})

@app.get("/jugadores/{id}/edit", response_class=HTMLResponse)
async def edit_jugador_form(request: Request, id: int):
    jugadores = jugadores_handler.read_all(Jugador)
    jugador = next((j for j in jugadores if j.id == id), None)
    if not jugador:
        raise NotFoundException("Jugador", str(id))
    return templates.TemplateResponse("jugadores_edit.html", {"request": request, "jugador": jugador})

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
    method: str = Form(None)
):
    jugadores = jugadores_handler.read_all(Jugador)
    jugador = next((j for j in jugadores if j.id == id), None)
    if not jugador:
        raise NotFoundException("Jugador", str(id))
    if method == "DELETE":
        jugadores = [j for j in jugadores if j.id != id]
        jugadores_handler.write_all([j.dict() for j in jugadores])
        return RedirectResponse(url="/jugadores/", status_code=303)
    else:
        jugador_index = next(i for i, j in enumerate(jugadores) if j.id == id)
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
            activo=activo
        ).dict()
        jugadores[jugador_index] = updated_jugador
        jugadores_handler.write_all(jugadores)
        return RedirectResponse(url=f"/jugadores/{id}", status_code=303)

# Rutas CRUD para Equipos (similar a Jugadores)
@app.get("/equipos/", response_class=HTMLResponse)
async def get_equipos(request: Request):
    equipos = equipos_handler.read_all(Equipo)
    return templates.TemplateResponse("equipos.html", {"request": request, "equipos": equipos})

@app.get("/equipos/crear/", response_class=HTMLResponse)
async def create_equipo_form(request: Request):
    return templates.TemplateResponse("equipos_crear.html", {"request": request})

@app.post("/equipos/")
async def create_equipo(
    nombre: str = Form(...),
    pais: str = Form(...),
    enfrentamientos_con_colombia: int = Form(...)
):
    equipos = equipos_handler.read_all(Equipo)
    new_id = max([e.id for e in equipos] + [0]) + 1
    new_equipo = Equipo(
        id=new_id,
        nombre=nombre,
        pais=pais,
        enfrentamientos_con_colombia=enfrentamientos_con_colombia
    ).dict()
    equipos.append(new_equipo)
    equipos_handler.write_all(equipos)
    return RedirectResponse(url=f"/equipos/{new_id}", status_code=303)

@app.get("/equipos/{id}", response_class=HTMLResponse)
async def get_equipo(request: Request, id: int):
    equipos = equipos_handler.read_all(Equipo)
    equipo = next((e for e in equipos if e.id == id), None)
    if not equipo:
        raise NotFoundException("Equipo", str(id))
    return templates.TemplateResponse("equipo_detail.html", {"request": request, "equipo": equipo})

@app.get("/equipos/{id}/edit", response_class=HTMLResponse)
async def edit_equipo_form(request: Request, id: int):
    equipos = equipos_handler.read_all(Equipo)
    equipo = next((e for e in equipos if e.id == id), None)
    if not equipo:
        raise NotFoundException("Equipo", str(id))
    return templates.TemplateResponse("equipos_edit.html", {"request": request, "equipo": equipo})

@app.post("/equipos/{id}/")
async def update_equipo(
    id: int,
    nombre: str = Form(...),
    pais: str = Form(...),
    enfrentamientos_con_colombia: int = Form(...),
    method: str = Form(None)
):
    equipos = equipos_handler.read_all(Equipo)
    equipo = next((e for e in equipos if e.id == id), None)
    if not equipo:
        raise NotFoundException("Equipo", str(id))
    if method == "DELETE":
        equipos = [e for e in equipos if e.id != id]
        equipos_handler.write_all([e.dict() for e in equipos])
        return RedirectResponse(url="/equipos/", status_code=303)
    else:
        equipo_index = next(i for i, e in enumerate(equipos) if e.id == id)
        updated_equipo = Equipo(
            id=id,
            nombre=nombre,
            pais=pais,
            enfrentamientos_con_colombia=enfrentamientos_con_colombia
        ).dict()
        equipos[equipo_index] = updated_equipo
        equipos_handler.write_all(equipos)
        return RedirectResponse(url=f"/equipos/{id}", status_code=303)

# Rutas CRUD para Partidos (similar a Equipos)
@app.get("/partidos/", response_class=HTMLResponse)
async def get_partidos(request: Request):
    partidos = partidos_handler.read_all(Partido)
    return templates.TemplateResponse("partidos.html", {"request": request, "partidos": partidos})

@app.get("/partidos/crear/", response_class=HTMLResponse)
async def create_partido_form(request: Request):
    return templates.TemplateResponse("partidos_crear.html", {"request": request})

@app.post("/partidos/")
async def create_partido(
    equipo_local: str = Form(...),
    equipo_visitante: str = Form(...),
    fecha: date = Form(...),
    goles_local: int = Form(...),
    goles_visitante: int = Form(...),
    torneo_id: int = Form(...),
    eliminado: str = Form(...),
    tarjetas_amarillas_local: int = Form(...),
    tarjetas_amarillas_visitante: int = Form(...),
    tarjetas_rojas_local: int = Form(...),
    tarjetas_rojas_visitante: int = Form(...)
):
    partidos = partidos_handler.read_all(Partido)
    new_id = max([p.id for p in partidos] + [0]) + 1
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
    ).dict()
    partidos.append(new_partido)
    partidos_handler.write_all(partidos)
    return RedirectResponse(url=f"/partidos/{new_id}", status_code=303)

@app.get("/partidos/{id}", response_class=HTMLResponse)
async def get_partido(request: Request, id: int):
    partidos = partidos_handler.read_all(Partido)
    partido = next((p for p in partidos if p.id == id), None)
    if not partido:
        raise NotFoundException("Partido", str(id))
    return templates.TemplateResponse("partido_detail.html", {"request": request, "partido": partido})

@app.get("/partidos/{id}/edit", response_class=HTMLResponse)
async def edit_partido_form(request: Request, id: int):
    partidos = partidos_handler.read_all(Partido)
    partido = next((p for p in partidos if p.id == id), None)
    if not partido:
        raise NotFoundException("Partido", str(id))
    return templates.TemplateResponse("partidos_edit.html", {"request": request, "partido": partido})

@app.post("/partidos/{id}/")
async def update_partido(
    id: int,
    equipo_local: str = Form(...),
    equipo_visitante: str = Form(...),
    fecha: date = Form(...),
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
    partidos = partidos_handler.read_all(Partido)
    partido = next((p for p in partidos if p.id == id), None)
    if not partido:
        raise NotFoundException("Partido", str(id))
    if method == "DELETE":
        partidos = [p for p in partidos if p.id != id]
        partidos_handler.write_all([p.dict() for p in partidos])
        return RedirectResponse(url="/partidos/", status_code=303)
    else:
        partido_index = next(i for i, p in enumerate(partidos) if p.id == id)
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
        ).dict()
        partidos[partido_index] = updated_partido
        partidos_handler.write_all(partidos)
        return RedirectResponse(url=f"/partidos/{id}", status_code=303)

# Rutas CRUD para Torneos (similar a Equipos)
@app.get("/torneos/", response_class=HTMLResponse)
async def get_torneos(request: Request):
    torneos = torneos_handler.read_all(Torneo)
    return templates.TemplateResponse("torneos.html", {"request": request, "torneos": torneos})

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
    torneos = torneos_handler.read_all(Torneo)
    new_id = max([t.id for t in torneos] + [0]) + 1
    new_torneo = Torneo(
        id=new_id,
        nombre=nombre,
        anio=anio,
        pais_anfitrion=pais_anfitrion,
        estado=estado,
        eliminado=eliminado
    ).dict()
    torneos.append(new_torneo)
    torneos_handler.write_all(torneos)
    return RedirectResponse(url=f"/torneos/{new_id}", status_code=303)

@app.get("/torneos/{id}", response_class=HTMLResponse)
async def get_torneo(request: Request, id: int):
    torneos = torneos_handler.read_all(Torneo)
    torneo = next((t for t in torneos if t.id == id), None)
    if not torneo:
        raise NotFoundException("Torneo", str(id))
    return templates.TemplateResponse("torneo_detail.html", {"request": request, "torneo": torneo})

@app.get("/torneos/{id}/edit", response_class=HTMLResponse)
async def edit_torneo_form(request: Request, id: int):
    torneos = torneos_handler.read_all(Torneo)
    torneo = next((t for t in torneos if t.id == id), None)
    if not torneo:
        raise NotFoundException("Torneo", str(id))
    return templates.TemplateResponse("torneos_edit.html", {"request": request, "torneo": torneo})

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
    torneos = torneos_handler.read_all(Torneo)
    torneo = next((t for t in torneos if t.id == id), None)
    if not torneo:
        raise NotFoundException("Torneo", str(id))
    if method == "DELETE":
        torneos = [t for t in torneos if t.id != id]
        torneos_handler.write_all([t.dict() for t in torneos])
        return RedirectResponse(url="/torneos/", status_code=303)
    else:
        torneo_index = next(i for i, t in enumerate(torneos) if t.id == id)
        updated_torneo = Torneo(
            id=id,
            nombre=nombre,
            anio=anio,
            pais_anfitrion=pais_anfitrion,
            estado=estado,
            eliminado=eliminado
        ).dict()
        torneos[torneo_index] = updated_torneo
        torneos_handler.write_all(torneos)
        return RedirectResponse(url=f"/torneos/{id}", status_code=303)

# Rutas CRUD para Plantillas (similar a Equipos)
@app.get("/plantillas/", response_class=HTMLResponse)
async def get_plantillas(request: Request):
    plantillas = plantillas_handler.read_all(Plantilla)
    return templates.TemplateResponse("plantillas.html", {"request": request, "plantillas": plantillas})

@app.get("/plantillas/crear/", response_class=HTMLResponse)
async def create_plantilla_form(request: Request):
    return templates.TemplateResponse("plantillas_crear.html", {"request": request})

@app.post("/plantillas/")
async def create_plantilla(
    equipo_id: int = Form(...),
    nombre: str = Form(None),
    posicion: str = Form(None),
    anio: int = Form(...),
    torneo_id: int = Form(None),
    jugador_id: int = Form(None)
):
    plantillas = plantillas_handler.read_all(Plantilla)
    new_id = max([p.id for p in plantillas] + [0]) + 1
    new_plantilla = Plantilla(
        id=new_id,
        equipo_id=equipo_id,
        nombre=nombre,
        posicion=posicion,
        anio=anio,
        torneo_id=torneo_id,
        jugador_id=jugador_id
    ).dict()
    plantillas.append(new_plantilla)
    plantillas_handler.write_all(plantillas)
    return RedirectResponse(url=f"/plantillas/{new_id}", status_code=303)

@app.get("/plantillas/{id}", response_class=HTMLResponse)
async def get_plantilla(request: Request, id: int):
    plantillas = plantillas_handler.read_all(Plantilla)
    plantilla = next((p for p in plantillas if p.id == id), None)
    if not plantilla:
        raise NotFoundException("Plantilla", str(id))
    return templates.TemplateResponse("plantilla_detail.html", {"request": request, "plantilla": plantilla})

@app.get("/plantillas/{id}/edit", response_class=HTMLResponse)
async def edit_plantilla_form(request: Request, id: int):
    plantillas = plantillas_handler.read_all(Plantilla)
    plantilla = next((p for p in plantillas if p.id == id), None)
    if not plantilla:
        raise NotFoundException("Plantilla", str(id))
    return templates.TemplateResponse("plantillas_edit.html", {"request": request, "plantilla": plantilla})

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
    plantillas = plantillas_handler.read_all(Plantilla)
    plantilla = next((p for p in plantillas if p.id == id), None)
    if not plantilla:
        raise NotFoundException("Plantilla", str(id))
    if method == "DELETE":
        plantillas = [p for p in plantillas if p.id != id]
        plantillas_handler.write_all([p.dict() for p in plantillas])
        return RedirectResponse(url="/plantillas/", status_code=303)
    else:
        plantilla_index = next(i for i, p in enumerate(plantillas) if p.id == id)
        updated_plantilla = Plantilla(
            id=id,
            equipo_id=equipo_id,
            nombre=nombre,
            posicion=posicion,
            anio=anio,
            torneo_id=torneo_id,
            jugador_id=jugador_id
        ).dict()
        plantillas[plantilla_index] = updated_plantilla
        plantillas_handler.write_all(plantillas)
        return RedirectResponse(url=f"/plantillas/{id}", status_code=303)