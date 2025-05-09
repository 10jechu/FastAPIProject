Jesús Manuel Vilardi González 67001298\
API Proyecto Selección Colombia 2021-2024
Descripción General
Este proyecto es una aplicación FastAPI para gestionar datos relacionados con el fútbol, incluyendo partidos, jugadores, torneos, equipos y plantillas. La API proporciona operaciones CRUD para cada entidad, con los datos almacenados en archivos CSV. Incluye capacidades de filtrado y manejo adecuado de excepciones HTTP.
Requisitos

Modelos: Mínimo 2 modelos (implementados: Partido, Jugador, Torneo, Equipo, Plantilla).
CRUD: Operaciones CRUD completas para cada modelo.
Persistencia: Datos almacenados en archivos CSV (uno por modelo).
Manejo de Excepciones: Excepciones HTTP para errores (ej. 404 para no encontrado, 400 para duplicados).
Separación de Responsabilidades: Las operaciones están separadas de los endpoints, con utilidades en módulos separados.
Filtrado: Al menos un modelo soporta filtrado (implementado para Partido y Jugador).
Buscador: Búsqueda por un criterio diferente a ID (implementado mediante filtrado por año).
Trazabilidad: Trazabilidad en eliminaciones (pendiente de implementar).
Mapa de Endpoints: Documentado a continuación.

Mapa de Endpoints

Método
Endpoint
Descripción



GET
/partidos/
Obtiene una lista de todos los partidos.


GET
/partidos/{partido_id}
Obtiene un partido específico por su ID.


GET
/partidos/filter/{ano}
Filtra los partidos por año (ej. 2024).


POST
/partidos/
Crea un nuevo partido.


PUT
/partidos/{partido_id}
Actualiza un partido existente por su ID.


DELETE
/partidos/{partido_id}
Elimina un partido por su ID.


Jugadores



Método
Endpoint
Descripción



GET
/jugadores/
Obtiene una lista de todos los jugadores.


GET
/jugadores/{jugador_id}
Obtiene un jugador específico por su ID.


GET
/jugadores/filter/{ano}
Filtra los jugadores por año (ej. 2024).


POST
/jugadores/
Crea un nuevo jugador.


PUT
/jugadores/{jugador_id}
Actualiza un jugador existente por su ID.


DELETE
/jugadores/{jugador_id}
Elimina un jugador por su ID.


Torneos



Método
Endpoint
Descripción



GET
/torneos/
Obtiene una lista de todos los torneos.


GET
/torneos/{torneo_id}
Obtiene un torneo específico por su ID.


POST
/torneos/
Crea un nuevo torneo.


PUT
/torneos/{torneo_id}
Actualiza un torneo existente por su ID.


DELETE
/torneos/{torneo_id}
Elimina un torneo por su ID.


Equipos



Método
Endpoint
Descripción



GET
/equipos/
Obtiene una lista de todos los equipos.


GET
/equipos/{equipo_id}
Obtiene un equipo específico por su ID.


POST
/equipos/
Crea un nuevo equipo.


PUT
/equipos/{equipo_id}
Actualiza un equipo existente por su ID.


DELETE
/equipos/{equipo_id}
Elimina un equipo por su ID.


Plantillas



Método
Endpoint
Descripción



GET
/plantillas/
Obtiene una lista de todas las entradas de plantillas.


GET
/plantillas/{plantilla_id}
Obtiene una entrada de plantilla específica por su ID.


POST
/plantillas/
Crea una nueva entrada de plantilla.


PUT
/plantillas/{plantilla_id}
Actualiza una entrada de plantilla existente por su ID.


DELETE
/plantillas/{plantilla_id}
Elimina una entrada de plantilla por su ID.


Uso

Inicia el servidor FastAPI:
uvicorn main:app --reload


Accede a la documentación de la API:

Swagger UI: http://127.0.0.1:8000/docs
ReDoc: http://127.0.0.1:8000/redoc


Prueba los endpoints usando Swagger UI o una herramienta como Postman.


Notas

Los endpoints de Plantilla pueden tener problemas debido a desajustes con el CSV, que se corregirán más adelante.
La trazabilidad en las eliminaciones (ej. registrar los registros eliminados) aún no está implementada, pero se puede agregar como una mejora futura.

también con las correciones de solangie  manejos exepciones
activo o inactivo de jugadores para empezar


