"""
Configuracion central del bot GOTC.

Edita este archivo para cambiar el comportamiento del bot sin tocar
la logica principal en search_bot.py.
"""

# ============================================================
# AJUSTES FRECUENTES
# ============================================================

# Cantidad exacta de ataques que debe recibir cada enemigo.
# Aplica sin importar si FARM_EVENT o ELITE_CREATURE estan activos.
NUM_ATTACKS = 5

# True  -> farmear desde Events.
# False -> usar busqueda directa.
FARM_EVENT = True

# Marca si la criatura buscada es elite. No cambia la cantidad de ataques.
ELITE_CREATURE = False

# Evento que queremos farmear, contando de arriba hacia abajo.
EVENT_NUMBER = 1

# Maximo de movimientos de camara antes de abandonar la busqueda.
MAX_MOVES = 40


# ============================================================
# RECUPERACION AUTOMATICA
# ============================================================

# UNKNOWN puede aparecer temporalmente mientras GOTC procesa.
# Solo consideraremos que hay un problema si permanece asi
# durante este numero de segundos consecutivos.
MAX_UNKNOWN_SECONDS = 10.0

# Tiempo entre capturas cuando estamos esperando que termine
# una transicion.
UNKNOWN_POLL_INTERVAL = 0.5

# Cantidad maxima de BACK consecutivos para intentar volver
# a un estado conocido antes de detener el bot.
MAX_RECOVERY_BACKS = 8

# Espera despues de cada BACK de recuperacion.
RECOVERY_BACK_DELAY = 1.0


# ============================================================
# EVENTOS Y NAVEGACION
# ============================================================

# Coordenadas de navegacion.
COMPASS_X = 693
COMPASS_Y = 837

EVENTS_X = 1000
EVENTS_Y = 300

SEARCH_X = 1000
SEARCH_Y = 800

# Todos los eventos tienen aproximadamente 145 px de alto
# y estan separados por unos 20 px.
EVENT_X = 920
EVENT_FIRST_Y = 428
EVENT_SPACING_Y = 165

# Scroll de la lista de eventos.
EVENT_SCROLL_X = 920
EVENT_SCROLL_START_Y = 750
EVENT_SCROLL_END_Y = 450

# Tiempos para que se abran las distintas pantallas.
AFTER_COMPASS_DELAY = 1.0
AFTER_EVENTS_DELAY = 1.0
AFTER_EVENT_SELECT_DELAY = 1.0
AFTER_SEARCH_DELAY = 1.0
AFTER_EVENT_SCROLL_DELAY = 1.0


# ============================================================
# ATAQUE Y MARCHAS
# ============================================================

TARGET_X = 920
TARGET_Y_FIRST = 320

# Los siguientes ataques al mismo enemigo usan esta Y.
TARGET_Y_REPEAT = 520

AFTER_TARGET_TAP_DELAY = 1.0
AFTER_ATTACK_DELAY = 1.0
AFTER_MARCH_DELAY = 1.5

# Boton CANCEL de "ADD MARCH SLOTS".
CANCEL_NO_MARCH_X = 810
CANCEL_NO_MARCH_Y = 780

# Cuanto esperar antes de volver a comprobar si regreso una marcha.
MARCH_RETRY_DELAY = 20.0

# Espera despues de pulsar Go To o Next.
AFTER_GO_TO_DELAY = 3.0


# ============================================================
# TEMPLATES Y DETECCION VISUAL
# ============================================================

THRESHOLDS = {
    "IDLE": 0.90,
    "GO_TO": 0.90,
    "NEXT": 0.90,
    "MOVE_CAMERA": 0.85,
    "RECOVER_COMPASS": 0.85,
}

TEMPLATES = {
    "IDLE": "idle.png",
    "GO_TO": "go_to.png",
    "NEXT": "next.png",
    "MOVE_CAMERA": "move_camera.png",
    "RECOVER_COMPASS": "recover_compass.png",
}

TEMPLATE_FALLBACKS = {
    "RECOVER_COMPASS": "restart_compass.png",
}

ATTACK_TEMPLATE = "attack.png"
ATTACK_THRESHOLD = 0.90

MARCH_TEMPLATE = "march.png"
MARCH_THRESHOLD = 0.856

NO_MARCH_TEMPLATE = "no_march.png"
NO_MARCH_THRESHOLD = 0.90

STOP_TEMPLATE = "stop.png"
STOP_THRESHOLD = 0.90


# ============================================================
# MOVIMIENTO DEL MAPA
# ============================================================

# Pequena espera despues de mover el mapa.
AFTER_SWIPE_DELAY = 0.5

# Centro aproximado de la zona segura del mapa.
CENTER_X = 920
CENTER_Y = 520

# Distancia de cada swipe.
SWIPE_DISTANCE_X = 1100
SWIPE_DISTANCE_Y = 650

# Duracion del swipe en milisegundos.
SWIPE_DURATION = 600

MAP_LEFT = 700
MAP_RIGHT = 1140
MAP_TOP = 260
MAP_BOTTOM = 700


# ============================================================
# NOTIFICACIONES
# ============================================================

NTFY_TOPIC = "gotc_bot_notificatios_123456789"
NTFY_URL = f"https://ntfy.sh/{NTFY_TOPIC}"
NTFY_TIMEOUT = 5


# ============================================================
# SISTEMA
# ============================================================

PNG_SIGNATURE = b"\x89PNG\r\n\x1a\n"
