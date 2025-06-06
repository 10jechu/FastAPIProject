from fastapi import FastAPI, Request, Form, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import os
from operations.equipo_ops import EquipoOps
from operations.jugador_ops import JugadorOps
from operations.partido_ops import PartidoOps
from operations.plantilla_ops import PlantillaOps
from operations.torneo_ops import TorneoOps
from models.equipo import Equipo
from models.jugador import Jugador
from models.partido import Partido
from models.plantilla import Plantilla
from models.torneo import Torneo
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

# Instanciar operaciones
equipo_ops = EquipoOps(EQUIPOS_CSV)
jugador_ops = JugadorOps(JUGADORES_CSV)
partido_ops = PartidoOps(PARTIDOS_CSV)
torneo_ops = TorneoOps(TORNEOS_CSV)
plantilla_ops = PlantillaOps(PLANTILLAS_CSV, equipo_ops)

# Rutas CRUD para Jugadores
@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
    jugadores = jugador_ops.get_all()
    equipos = equipo_ops.get_all()
    partidos = partido_ops.get_all()
    torneos = torneo_ops.get_all()
    plantillas = plantilla_ops.get_all()
    return templates.TemplateResponse(
        "index.html",
        {"request": request, "jugadores": jugadores, "equipos": equipos, "partidos": partidos, "torneos": torneos, "plantillas": plantillas}
    )

@app.get("/jugadores/", response_class=HTMLResponse)
async def get_jugadores(request: Request):
    jugadores = jugador_ops.get_all()
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
    new_jugador = Jugador(
        id=0,  # ID se generará en JugadorOps.create
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
    try:
        jugador_ops.create(new_jugador)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
    return RedirectResponse(url="/jugadores/", status_code=303)

@app.get("/jugadores/{id}", response_class=HTMLResponse)
async def get_jugador(request: Request, id: int):
    try:
        jugador = jugador_ops.get_by_id(id)
    except Exception as e:
        raise HTTPException(status_code=404, detail=str(e))
    return templates.TemplateResponse("jugador_detail.html", {"request": request, "jugador": jugador})

@app.get("/jugadores/{id}/edit", response_class=HTMLResponse)
async def edit_jugador_form(request: Request, id: int):
    try:
        jugador = jugador_ops.get_by_id(id)
    except Exception as e:
        raise HTTPException(status_code=404, detail=str(e))
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
    try:
        jugador = jugador_ops.get_by_id(id)
    except Exception as e:
        raise HTTPException(status_code=404, detail=str(e))
    if method == "DELETE":
        try:
            jugador_ops.delete(id)
        except Exception as e:
            raise HTTPException(status_code=400, detail=str(e))
        return RedirectResponse(url="/jugadores/", status_code=303)
    else:
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
        )
        try:
            jugador_ops.update(id, updated_jugador)
        except Exception as e:
            raise HTTPException(status_code=400, detail=str(e))
        return RedirectResponse(url=f"/jugadores/{id}", status_code=303)

# Rutas CRUD para Equipos (similar a Jugadores)
@app.get("/equipos/", response_class=HTMLResponse)
async def get_equipos(request: Request):
    equipos = equipo_ops.get_all()
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
    new_equipo = Equipo(
        id=0,  # ID se generará en EquipoOps.create
        nombre=nombre,
        pais=pais,
        enfrentamientos_con_colombia=enfrentamientos_con_colombia
    )
    try:
        equipo_ops.create(new_equipo)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
    return RedirectResponse(url="/equipos/", status_code=303)

@app.get("/equipos/{id}", response_class=HTMLResponse)
async def get_equipo(request: Request, id: int):
    try:
        equipo = equipo_ops.get_by_id(str(id))
    except Exception as e:
        raise HTTPException(status_code=404, detail=str(e))
    return templates.TemplateResponse("equipo_detail.html", {"request": request, "equipo": equipo})

@app.get("/equipos/{id}/edit", response_class=HTMLResponse)
async def edit_equipo_form(request: Request, id: int):
    try:
        equipo = equipo_ops.get_by_id(str(id))
    except Exception as e:
        raise HTTPException(status_code=404, detail=str(e))
    return templates.TemplateResponse("equipos_edit.html", {"request": request, "equipo": equipo})

@app.post("/equipos/{id}/")
async def update_equipo(
    id: int,
    nombre: str = Form(...),
    pais: str = Form(...),
    enfrentamientos_con_colombia: int = Form(...),
    method: str = Form(None)
):
    try:
        equipo = equipo_ops.get_by_id(str(id))
    except Exception as e:
        raise HTTPException(status_code=404, detail=str(e))
    if method == "DELETE":
        try:
            equipo_ops.delete(str(id))
        except Exception as e:
            raise HTTPException(status_code=400, detail=str(e))
        return RedirectResponse(url="/equipos/", status_code=303)
    else:
        updated_equipo = Equipo(
            id=id,
            nombre=nombre,
            pais=pais,
            enfrentamientos_con_colombia=enfrentamientos_con_colombia
        )
        try:
            equipo_ops.update(str(id), updated_equipo)
        except Exception as e:
            raise HTTPException(status_code=400, detail=str(e))
        return RedirectResponse(url=f"/equipos/{id}", status_code=303)

# (Rutas para partidos, torneos, plantillas similares, ajusta según necesidad)