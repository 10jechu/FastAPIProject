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

app = FastAPI(title="Selección Colombia - Gestión")
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

# Rutas de los archivos CSV
JUGADORES_CSV = "data/jugadores.csv"
EQUIPOS_CSV = "data/equipos.csv"
PARTIDOS_CSV = "data/partidos.csv"
TORNEOS_CSV = "data/torneos.csv"

# Modelos Pydantic
class Jugador(BaseModel):
    id: int
    nombre: str
    fecha_nacimiento: str
    club: str
    altura: str
    pie: str
    partidos: int
    goles: int
    numero_camisa: int
    anio: int
    posicion: str
    activo: bool
    imagen: Optional[str] = None

    @classmethod
    def validate_image(cls, imagen: str) -> Optional[str]:
        if not imagen or pd.isna(imagen):
            return None
        if not imagen.startswith(('http://', 'https://')) and not imagen.endswith('.png'):
            return None
        return imagen

class Equipo(BaseModel):
    id: int
    nombre: str
    pais: str
    enfrentamientos_con_colombia: int
    bandera: Optional[str] = None

    @classmethod
    def validate_bandera(cls, bandera: str) -> Optional[str]:
        if not bandera or pd.isna(bandera):
            return None
        if not bandera.startswith(('http://', 'https://')) and not bandera.endswith('.png'):
            return None
        return bandera

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

class Torneo(BaseModel):
    id: int
    nombre: str
    anio: int
    eliminado: str
    pais_anfitrion: Optional[str] = None
    estado: Optional[str] = None
    imagen: Optional[str] = None

    @classmethod
    def validate_image(cls, imagen: str) -> Optional[str]:
        if not imagen or pd.isna(imagen):
            return None
        if not imagen.startswith(('http://', 'https://')) and not imagen.endswith('.png'):
            return None
        return imagen

# Funciones de carga y actualización de datos
def load_csv(csv_file):
    if not os.path.exists(csv_file):
        with open(csv_file, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow([])  # Crear archivo vacío con encabezado
        return []
    df = pd.read_csv(csv_file)
    if csv_file == JUGADORES_CSV:
        column_mapping = {
            'Jugadores': 'nombre',
            'F_Nacim_Edad': 'fecha_nacimiento',
            'Club': 'club',
            'Altura': 'altura',
            'Pie': 'pie',
            'Partidos_con_la_seleccion': 'partidos',
            'Goles': 'goles',
            'Numero_de_camisa': 'numero_camisa',
            'anio': 'anio',
            'posicion': 'posicion',
            'activo': 'activo'
        }
        df = df.rename(columns=column_mapping)
        for col in ['nombre', 'fecha_nacimiento', 'club', 'altura', 'pie', 'partidos', 'goles', 'numero_camisa', 'anio', 'posicion', 'activo', 'imagen']:
            if col not in df.columns:
                df[col] = None
        df['id'] = df['id'].fillna(0).astype(int)
        df['partidos'] = df['partidos'].fillna(0).astype(int)
        df['goles'] = df['goles'].fillna(0).astype(int)
        df['numero_camisa'] = df['numero_camisa'].fillna(0).astype(int)
        df['anio'] = df['anio'].fillna(2025).astype(int)
        df['activo'] = df['activo'].fillna(False).astype(bool)
    elif csv_file == EQUIPOS_CSV:
        for col in ['nombre', 'pais', 'enfrentamientos_con_colombia', 'bandera']:
            if col not in df.columns:
                df[col] = None
        df['id'] = df['id'].fillna(0).astype(int)
        df['enfrentamientos_con_colombia'] = df['enfrentamientos_con_colombia'].fillna(0).astype(int)
    elif csv_file == TORNEOS_CSV:
        for col in ['nombre', 'anio', 'eliminado', 'pais_anfitrion', 'estado', 'imagen']:
            if col not in df.columns:
                df[col] = None
        df['id'] = df['id'].fillna(0).astype(int)
        df['anio'] = df['anio'].fillna(2025).astype(int)
    for column in df.columns:
        if column in ['imagen', 'bandera', 'pais_anfitrion', 'estado', 'torneo_id', 'eliminado']:
            df[column] = df[column].apply(lambda x: str(x).strip() if isinstance(x, str) and pd.notna(x) else None)
        elif df[column].dtype in ['float64', 'int64']:
            df[column] = df[column].apply(lambda x: 0 if pd.isna(x) else x)
    if 'imagen' in df.columns:
        df['imagen'] = df['imagen'].apply(lambda x: Jugador.validate_image(x) if csv_file == JUGADORES_CSV else Torneo.validate_image(x))
    if 'bandera' in df.columns:
        df['bandera'] = df['bandera'].apply(lambda x: Equipo.validate_bandera(x))
    return df.to_dict(orient="records")

def update_csv(data_list, csv_file, new_item=None):
    data_dicts = [item.dict(exclude_unset=True) for item in data_list]
    if new_item:
        if isinstance(new_item, (Jugador, Equipo, Partido, Torneo)):
            data_dicts.append(new_item.dict(exclude_unset=True))
    fieldnames = list(dict.fromkeys([key for item in data_dicts for key in item.keys()]))
    with open(csv_file, mode='w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(data_dicts)
    return data_list

def load_jugadores(): return [Jugador(**item) for item in load_csv(JUGADORES_CSV)]
def load_equipos(): return [Equipo(**item) for item in load_csv(EQUIPOS_CSV)]
def load_partidos(): return [Partido(**item) for item in load_csv(PARTIDOS_CSV)]
def load_torneos(): return [Torneo(**item) for item in load_csv(TORNEOS_CSV)]

# Rutas para Jugadores
@app.get("/jugadores/", response_class=HTMLResponse)
async def get_jugadores(request: Request, year: Optional[int] = None):
    jugadores = load_jugadores()
    if year:
        jugadores = [j for j in jugadores if j.anio == year]
    return templates.TemplateResponse("jugadores.html", {"request": request, "jugadores": jugadores, "year": year})

@app.get("/jugadores/crear/", response_class=HTMLResponse)
async def create_jugador_form(request: Request):
    return templates.TemplateResponse("jugadores_crear.html", {"request": request})

@app.post("/jugadores/crear/")
async def create_jugador(
    nombre: str = Form(...), fecha_nacimiento: str = Form(...), club: str = Form(...),
    altura: str = Form(...), pie: str = Form(...), partidos: int = Form(...),
    goles: int = Form(...), numero_camisa: int = Form(...), anio: int = Form(...),
    posicion: str = Form(...), activo: bool = Form(False), imagen: str = Form("")
):
    jugadores = load_jugadores()
    new_id = max([j.id for j in jugadores] + [0]) + 1
    imagen_validada = Jugador.validate_image(imagen) if imagen else None
    new_jugador = Jugador(id=new_id, nombre=nombre, fecha_nacimiento=fecha_nacimiento, club=club,
                          altura=altura, pie=pie, partidos=partidos, goles=goles,
                          numero_camisa=numero_camisa, anio=anio, posicion=posicion,
                          activo=activo, imagen=imagen_validada)
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
    id: int, nombre: str = Form(...), fecha_nacimiento: str = Form(...), club: str = Form(...),
    altura: str = Form(...), pie: str = Form(...), partidos: int = Form(...),
    goles: int = Form(...), numero_camisa: int = Form(...), anio: int = Form(...),
    posicion: str = Form(...), activo: bool = Form(False), imagen: str = Form("")
):
    jugadores = load_jugadores()
    jugador = next((j for j in jugadores if j.id == id), None)
    if not jugador:
        raise HTTPException(status_code=404, detail="Jugador no encontrado")
    imagen_validada = Jugador.validate_image(imagen) if imagen else None
    jugador.nombre = nombre
    jugador.fecha_nacimiento = fecha_nacimiento
    jugador.club = club
    jugador.altura = altura
    jugador.pie = pie
    jugador.partidos = partidos
    jugador.goles = goles
    jugador.numero_camisa = numero_camisa
    jugador.anio = anio
    jugador.posicion = posicion
    jugador.activo = activo
    jugador.imagen = imagen_validada
    update_csv(jugadores, JUGADORES_CSV)
    return RedirectResponse(url="/jugadores/", status_code=303)

@app.get("/jugadores/{id}/delete")
async def delete_jugador(id: int):
    jugadores = load_jugadores()
    jugador = next((j for j in jugadores if j.id == id), None)
    if jugador:
        jugadores = [j for j in jugadores if j.id != id]
        update_csv(jugadores, JUGADORES_CSV)
    return RedirectResponse(url="/jugadores/", status_code=303)

@app.get("/jugadores/{id}", response_class=HTMLResponse)
async def get_jugador_detalle(request: Request, id: int):
    jugadores = load_jugadores()
    jugador = next((j for j in jugadores if j.id == id), None)
    if not jugador:
        raise HTTPException(status_code=404, detail="Jugador no encontrado")
    return templates.TemplateResponse("jugador_detail.html", {"request": request, "jugador": jugador})

# Rutas para Equipos
@app.get("/equipos/", response_class=HTMLResponse)
async def get_equipos(request: Request, year: Optional[int] = None):
    equipos = load_equipos()
    print("Equipos cargados:", equipos)  # Depuración
    if year:
        equipos = [e for e in equipos if any(p.fecha.startswith(str(year)) for p in load_partidos() if e.nombre in [p.equipo_local, p.equipo_visitante])]
    return templates.TemplateResponse("equipos.html", {"request": request, "equipos": equipos, "year": year})

@app.get("/equipos/crear/", response_class=HTMLResponse)
async def create_equipo_form(request: Request):
    return templates.TemplateResponse("equipos_crear.html", {"request": request})

@app.post("/equipos/crear/")
async def create_equipo(nombre: str = Form(...), pais: str = Form(...), enfrentamientos_con_colombia: int = Form(...), bandera: str = Form("")):
    equipos = load_equipos()
    new_id = max([e.id for e in equipos] + [0]) + 1
    bandera_validada = Equipo.validate_bandera(bandera) if bandera else None
    new_equipo = Equipo(id=new_id, nombre=nombre, pais=pais, enfrentamientos_con_colombia=enfrentamientos_con_colombia, bandera=bandera_validada)
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
async def update_equipo(id: int, nombre: str = Form(...), pais: str = Form(...), enfrentamientos_con_colombia: int = Form(...), bandera: str = Form("")):
    equipos = load_equipos()
    equipo = next((e for e in equipos if e.id == id), None)
    if not equipo:
        raise HTTPException(status_code=404, detail="Equipo no encontrado")
    bandera_validada = Equipo.validate_bandera(bandera) if bandera else None
    equipo.nombre = nombre
    equipo.pais = pais
    equipo.enfrentamientos_con_colombia = enfrentamientos_con_colombia
    equipo.bandera = bandera_validada
    update_csv(equipos, EQUIPOS_CSV)
    return RedirectResponse(url="/equipos/", status_code=303)

@app.get("/equipos/{id}/delete")
async def delete_equipo(id: int):
    equipos = load_equipos()
    equipo = next((e for e in equipos if e.id == id), None)
    if equipo:
        equipos = [e for e in equipos if e.id != id]
        update_csv(equipos, EQUIPOS_CSV)
    return RedirectResponse(url="/equipos/", status_code=303)

@app.get("/equipos/{id}", response_class=HTMLResponse)
async def get_equipo_detalle(request: Request, id: int):
    equipos = load_equipos()
    equipo = next((e for e in equipos if e.id == id), None)
    if not equipo:
        raise HTTPException(status_code=404, detail="Equipo no encontrado")
    return templates.TemplateResponse("equipo_detail.html", {"request": request, "equipo": equipo})

# Rutas para Partidos
@app.get("/partidos/", response_class=HTMLResponse)
async def get_partidos(request: Request, year: Optional[int] = None):
    partidos = load_partidos()
    torneos = load_torneos()
    torneos_dict = {t.id: t for t in torneos}
    if year:
        partidos = [p for p in partidos if p.fecha and p.fecha.startswith(str(year))]
    return templates.TemplateResponse("partidos.html", {"request": request, "partidos": partidos, "torneos_dict": torneos_dict, "year": year})

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
    return RedirectResponse(url="/partidos/", status_code=303)

@app.get("/partidos/{id}", response_class=HTMLResponse)
async def get_partido_detalle(request: Request, id: int):
    partidos = load_partidos()
    partido = next((p for p in partidos if p.id == id), None)
    if not partido:
        raise HTTPException(status_code=404, detail="Partido no encontrado")
    torneos = load_torneos()
    torneos_dict = {t.id: t for t in torneos}
    return templates.TemplateResponse("partido_detail.html", {"request": request, "partido": partido, "torneos_dict": torneos_dict})

# Rutas para Torneos
@app.get("/torneos/", response_class=HTMLResponse)
async def get_torneos(request: Request, year: Optional[int] = None):
    torneos = load_torneos()
    if year:
        torneos = [t for t in torneos if t.anio == year]
    return templates.TemplateResponse("torneos.html", {"request": request, "torneos": torneos, "year": year})

@app.get("/torneos/crear/", response_class=HTMLResponse)
async def create_torneo_form(request: Request):
    return templates.TemplateResponse("torneos_crear.html", {"request": request})

@app.post("/torneos/crear/")
async def create_torneo(nombre: str = Form(...), anio: int = Form(...), eliminado: str = Form(...),
                       pais_anfitrion: str = Form(""), estado: str = Form(""), imagen: str = Form(...)):
    torneos = load_torneos()
    new_id = max([t.id for t in torneos] + [0]) + 1
    imagen_validada = Torneo.validate_image(imagen)
    new_torneo = Torneo(id=new_id, nombre=nombre, anio=anio, eliminado=eliminado,
                        pais_anfitrion=pais_anfitrion if pais_anfitrion else None,
                        estado=estado if estado else None, imagen=imagen_validada)
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
                       pais_anfitrion: str = Form(""), estado: str = Form(""), imagen: str = Form("")):
    torneos = load_torneos()
    torneo = next((t for t in torneos if t.id == id), None)
    if not torneo:
        raise HTTPException(status_code=404, detail="Torneo no encontrado")
    imagen_validada = Torneo.validate_image(imagen) if imagen else None
    torneo.nombre = nombre
    torneo.anio = anio
    torneo.eliminado = eliminado
    torneo.pais_anfitrion = pais_anfitrion if pais_anfitrion else None
    torneo.estado = estado if estado else None
    torneo.imagen = imagen_validada
    update_csv(torneos, TORNEOS_CSV)
    return RedirectResponse(url="/torneos/", status_code=303)

@app.get("/torneos/{id}/delete")
async def delete_torneo(id: int):
    torneos = load_torneos()
    torneo = next((t for t in torneos if t.id == id), None)
    if torneo:
        torneos = [t for t in torneos if t.id != id]
        update_csv(torneos, TORNEOS_CSV)
    return RedirectResponse(url="/torneos/", status_code=303)

@app.get("/torneos/{id}", response_class=HTMLResponse)
async def get_torneo_detalle(request: Request, id: int):
    torneos = load_torneos()
    torneo = next((t for t in torneos if t.id == id), None)
    if not torneo:
        raise HTTPException(status_code=404, detail="Torneo no encontrado")
    return templates.TemplateResponse("torneo_detail.html", {"request": request, "torneo": torneo})

# Rutas para Estadísticas
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

# Página principal y documentación
@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
    jugadores = load_jugadores()
    partidos = load_partidos()
    torneos = load_torneos()
    victorias_total = 0
    goles_total = 0
    partidos_jugados_total = 0
    for p in partidos:
        try:
            anio = p.fecha.split('-')[0] if p.fecha and '-' in p.fecha else "Sin año"
            if 2021 <= int(anio) <= 2024 and (p.equipo_local.lower() == "colombia" or p.equipo_visitante.lower() == "colombia"):
                partidos_jugados_total += 1
                goles_colombia = (p.goles_local if p.equipo_local.lower() == "colombia" else 0) + (p.goles_visitante if p.equipo_visitante.lower() == "colombia" else 0)
                goles_total += goles_colombia
                if (p.equipo_local.lower() == "colombia" and p.goles_local > p.goles_visitante) or (p.equipo_visitante.lower() == "colombia" and p.goles_visitante > p.goles_local):
                    victorias_total += 1
        except (IndexError, AttributeError, ValueError):
            continue
    return templates.TemplateResponse("index.html", {
        "request": request,
        "jugadores": jugadores,
        "victorias_total": victorias_total,
        "goles_total": goles_total,
        "partidos_jugados_total": partidos_jugados_total,
        "last_update": "10 de junio de 2025, 03:42 AM -05"
    })

@app.get("/documentacion/", response_class=HTMLResponse)
async def get_documentacion(request: Request):
    return templates.TemplateResponse("documentacion.html", {"request": request})