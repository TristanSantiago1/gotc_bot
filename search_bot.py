import subprocess
import time
import urllib.error
import urllib.request

import cv2
import numpy as np

from gotc_config import *

# ============================================================
# NOTIFICACIONES
# ============================================================

def send_ntfy_notification(title, message):
    """
    Publica una notificación simple en ntfy.

    Los errores de red no deben detener el bot.
    """

    request = urllib.request.Request(
        NTFY_URL,
        data=message.encode("utf-8"),
        method="POST",
        headers={
            "Title": title,
            "Priority": "default",
            "Tags": "video_game",
        },
    )

    try:
        with urllib.request.urlopen(
            request,
            timeout=NTFY_TIMEOUT
        ) as response:
            response.read()

    except urllib.error.URLError as error:
        print(
            "⚠ No se pudo enviar notificación ntfy: "
            f"{error}"
        )

def attacks_per_enemy():
    return NUM_ATTACKS

# ============================================================
# ADB
# ============================================================

def adb(*args):
    """
    Ejecuta un comando ADB.
    """

    return subprocess.run(
        ["adb", *args],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )


def keycode_back():
    """
    Envía BACK a Android mediante ADB.
    """

    print("  → KEYCODE_BACK")

    adb(
        "shell",
        "input",
        "keyevent",
        "KEYCODE_BACK"
    )


def tap(x, y):
    """
    Realiza un tap en coordenadas de la pantalla Android.
    """

    x = int(x)
    y = int(y)

    print(f"  → TAP ({x}, {y})")

    adb(
        "shell",
        "input",
        "tap",
        str(x),
        str(y)
    )


def swipe(x1, y1, x2, y2, duration=600):
    """
    Realiza un swipe mediante ADB.
    """

    print(
        f"  → SWIPE "
        f"({x1},{y1}) → ({x2},{y2})"
    )

    adb(
        "shell",
        "input",
        "swipe",
        str(x1),
        str(y1),
        str(x2),
        str(y2),
        str(duration)
    )


# ============================================================
# CAPTURA DE PANTALLA
# ============================================================

def screenshot():
    """
    Obtiene una captura directamente desde Waydroid.

    Waydroid puede insertar un warning antes de los bytes
    reales del PNG, así que buscamos manualmente la firma PNG.
    """

    result = adb(
        "exec-out",
        "screencap",
        "-p"
    )

    data = result.stdout

    start = data.find(PNG_SIGNATURE)

    if start == -1:
        raise RuntimeError(
            "No se encontró un PNG válido "
            "en la salida de ADB."
        )

    # Eliminar cualquier texto/warning anterior al PNG
    data = data[start:]

    image_array = np.frombuffer(
        data,
        dtype=np.uint8
    )

    image = cv2.imdecode(
        image_array,
        cv2.IMREAD_COLOR
    )

    if image is None:
        raise RuntimeError(
            "OpenCV no pudo decodificar "
            "la captura."
        )

    return image


# ============================================================
# TEMPLATES
# ============================================================

def load_templates():
    """
    Carga los templates utilizados para reconocer
    el estado de búsqueda.
    """

    templates = {}

    for name, filename in TEMPLATES.items():

        image = cv2.imread(filename)

        if image is None and name in TEMPLATE_FALLBACKS:

            fallback = TEMPLATE_FALLBACKS[name]

            print(
                f"⚠ No pude cargar {filename}. "
                f"Usando fallback {fallback}."
            )

            image = cv2.imread(fallback)

            filename = fallback

        if image is None:
            raise RuntimeError(
                f"No pude cargar el template: {filename}"
            )

        templates[name] = image

    return templates
    
def load_template(filename):
    image = cv2.imread(filename)

    if image is None:
        raise RuntimeError(
            f"No pude cargar el template: {filename}"
        )

    return image


# ============================================================
# TEMPLATE MATCHING
# ============================================================

def find_template(screen, template):
    """
    Busca un template dentro de la captura.

    Devuelve:
        confianza
        centro (x, y)
    """

    result = cv2.matchTemplate(
        screen,
        template,
        cv2.TM_CCOEFF_NORMED
    )

    _, confidence, _, location = cv2.minMaxLoc(
        result
    )

    h, w = template.shape[:2]

    center = (
        location[0] + w // 2,
        location[1] + h // 2
    )

    return confidence, center


def confirm_march(march_template):
    """
    Busca el botón MARCH y lo pulsa.

    Devuelve:
        True  -> encontró y pulsó MARCH
        False -> no encontró MARCH
    """

    print("→ Buscando botón MARCH...")

    for attempt in range(10):

        screen = screenshot()

        confidence, position = find_template(
            screen,
            march_template
        )

        print(
            f"MARCH intento {attempt + 1}/10 "
            f"| confianza: {confidence:.3f}"
        )

        if confidence >= MARCH_THRESHOLD:

            print(
                f"✓ MARCH detectado en {position}"
            )

            tap(*position)

            print("✓ Marcha enviada.")

            time.sleep(AFTER_MARCH_DELAY)

            return True

        time.sleep(0.5)

    print("✗ No apareció MARCH.")

    cv2.imwrite(
        "debug_march_not_found.png",
        screen
    )

    return False
    
def check_no_march(no_march_template):
    """
    Comprueba si apareció la ventana ADD MARCH SLOTS.

    True  -> no hay ninguna marcha disponible.
    False -> la ventana no está presente.
    """

    screen = screenshot()

    confidence, position = find_template(
        screen,
        no_march_template
    )

    print(
        f"NO_MARCH confianza: {confidence:.3f}"
    )

    if confidence >= NO_MARCH_THRESHOLD:

        print("⚠ No hay marchas disponibles.")
        print("→ Cerrando ADD MARCH SLOTS...")

        tap(
            CANCEL_NO_MARCH_X,
            CANCEL_NO_MARCH_Y
        )

        time.sleep(1.0)

        return True

    return False
    
    
def check_stop(stop_template):
    """
    Comprueba si apareció la pantalla de recarga
    por falta de stamina.

    True  -> stamina agotada
    False -> no apareció la pantalla
    """

    screen = screenshot()

    confidence, position = find_template(
        screen,
        stop_template
    )

    print(
        f"STOP confianza: {confidence:.3f}"
    )

    if confidence >= STOP_THRESHOLD:

        print()
        print("==========================")
        print(" 🛑 STAMINA AGOTADA")
        print("==========================")
        print(
            "Se detectó la pantalla de recarga."
        )
        print(
            "El bot se detendrá."
        )
        print()

        return True

    return False    
    

def attack_target(
    attack_template,
    march_template,
    no_march_template,
    stop_template,
    target_y
):
    """
    Intenta enviar UN ataque contra el enemigo actual.

    Devuelve:
        "SENT"      -> ataque enviado correctamente
        "STOP"      -> stamina agotada
        "NO_MARCH"  -> todas las marchas están ocupadas
        "RECOVER"   -> se perdió el estado esperado de la interfaz
    """

    print()
    print(
        f"→ Seleccionando objetivo en "
        f"({TARGET_X}, {target_y})"
    )

    tap(TARGET_X, target_y)

    time.sleep(AFTER_TARGET_TAP_DELAY)

    # ========================================================
    # BUSCAR ATTACK
    # ========================================================

    for attempt in range(10):

        screen = screenshot()

        confidence, position = find_template(
            screen,
            attack_template
        )

        print(
            f"ATTACK intento {attempt + 1}/10 "
            f"| confianza: {confidence:.3f}"
        )

        if confidence >= ATTACK_THRESHOLD:

            print(
                f"✓ ATTACK detectado en {position}"
            )

            tap(*position)

            time.sleep(AFTER_ATTACK_DELAY)

            # =================================================
            # ¿STAMINA AGOTADA?
            # =================================================

            if check_stop(stop_template):
                return "STOP"

            # =================================================
            # ¿NO HAY MARCHAS?
            # =================================================

            if check_no_march(no_march_template):
                return "NO_MARCH"

            # =================================================
            # HAY MARCHA: CONFIRMAR
            # =================================================

            if confirm_march(march_template):
                return "SENT"

            print(
                "⚠ No se pudo confirmar MARCH. "
                "Se solicitará recuperación."
            )

            return "RECOVER"

        time.sleep(0.5)

    print("⚠ No apareció ATTACK.")
    print(
        "→ Probablemente el tap al objetivo "
        "falló o el juego tuvo lag."
    )

    cv2.imwrite(
        "debug_attack_not_found.png",
        screen
    )

    return "RECOVER"
    
def attack_enemy_until_complete(
    attack_template,
    march_template,
    no_march_template,
    stop_template
):
    """
    Ataca al mismo enemigo exactamente la cantidad configurada.

    Mientras no haya marchas disponibles, mantiene el mismo
    objetivo y vuelve a intentarlo periódicamente.
    """

    attacks_done = 0
    target_attacks = attacks_per_enemy()
    first_target_position_used = False

    print()
    print("==========================")
    print(" INICIANDO CICLO DE ATAQUES")
    print("==========================")
    print(
        f"Objetivo: {target_attacks} ataques"
    )
    print()

    while attacks_done < target_attacks:

        attack_number = attacks_done + 1

        print(
            f"→ Intentando ataque "
            f"{attack_number}/"
            f"{target_attacks}"
        )

        # El primer ataque usa Y=320 porque acabamos
        # de llegar al objetivo mediante GO TO / NEXT.
        #
        # Los ataques posteriores usan Y=500.
        if not first_target_position_used:
            target_y = TARGET_Y_FIRST
            first_target_position_used = True
        else:
            target_y = TARGET_Y_REPEAT

        result = attack_target(
            attack_template,
            march_template,
            no_march_template,
            stop_template,
            target_y
        )
        
        # ====================================================
        # STAMINA AGOTADA
        # ====================================================

        if result == "STOP":

            print()
            print("==========================")
            print(" 🛑 BOT DETENIDO")
            print("==========================")
            print(
                "Motivo: stamina insuficiente."
            )
            print(
                f"Ataques completados en este objetivo: "
                f"{attacks_done}/{target_attacks}"
            )
            print()

            return "STOP"
        
        # ====================================================
        # ATAQUE ENVIADO
        # ====================================================

        if result == "SENT":

            attacks_done += 1

            print()
            print(
                f"✓ ATAQUE {attacks_done}/"
                f"{target_attacks} ENVIADO"
            )
            print()

            # Si todavía faltan ataques, volvemos a seleccionar
            # exactamente el mismo enemigo.
            if attacks_done < target_attacks:

                time.sleep(1.0)

            continue

        # ====================================================
        # SIN MARCHAS
        # ====================================================

        if result == "NO_MARCH":

            print()
            print(
                f"⏳ Ataque {attacks_done + 1}/"
                f"{target_attacks} pendiente."
            )

            print(
                f"→ Reintentando en "
                f"{MARCH_RETRY_DELAY:.0f} segundos..."
            )

            time.sleep(MARCH_RETRY_DELAY)

            # NO incrementamos attacks_done.
            # Volveremos a seleccionar el mismo enemigo.
            continue

        # ====================================================
        # ERROR
        # ====================================================

        if result == "RECOVER":

            print()
            print("==========================")
            print(" ⚠ RECUPERACIÓN NECESARIA")
            print("==========================")
            print(
                f"El ataque {attacks_done + 1}/"
                f"{target_attacks} NO fue contado."
            )
            print(
                "→ Regresando al controlador principal "
                "para reconocer la pantalla."
            )
            print()

            return "RECOVER"

    print()
    print("==========================")
    print(
        f" ✓ OBJETIVO COMPLETADO "
        f"({attacks_done}/{target_attacks})"
    )
    print("==========================")
    print()

    return "COMPLETE" 

# ============================================================
# DETECCIÓN DEL ESTADO
# ============================================================

def detect_state(screen, templates):
    """
    Determina cuál de los estados conocidos aparece.

    Estados posibles:

        IDLE
        GO_TO
        NEXT
        MOVE_CAMERA
        RECOVER_COMPASS
        UNKNOWN
    """

    results = {}

    for name, template in templates.items():

        confidence, position = find_template(
            screen,
            template
        )

        results[name] = {
            "confidence": confidence,
            "position": position
        }

    # Mostrar puntuaciones para poder diagnosticar
    print(
        " | ".join(
            f"{name}: {data['confidence']:.3f}"
            for name, data in results.items()
        )
    )

    # Solamente conservar detecciones que superan
    # el threshold correspondiente.
    valid = {
        name: data
        for name, data in results.items()
        if data["confidence"] >= THRESHOLDS[name]
    }

    # Ningún estado conocido
    if not valid:

        best_name = max(
            results,
            key=lambda name:
                results[name]["confidence"]
        )

        best = results[best_name]

        return (
            "UNKNOWN",
            best["confidence"],
            best["position"]
        )

    # Si más de uno supera su threshold,
    # nos quedamos con el de mayor confianza.
    best_name = max(
        valid,
        key=lambda name:
            valid[name]["confidence"]
    )

    best = valid[best_name]

    return (
        best_name,
        best["confidence"],
        best["position"]
    )


def recover_from_unknown(templates):
    """
    Intenta volver desde UNKNOWN a un estado conocido.

    Usa BACK para cerrar pantallas superpuestas. Si detecta
    RECOVER_COMPASS, pulsa donde debe estar la brújula para restaurarla.

    Devuelve:
        "RECOVERED" -> se volvió a un estado manejable
        "FAILED"    -> no se pudo recuperar con seguridad
    """

    print()
    print("==========================")
    print(" RECUPERANDO ESTADO")
    print("==========================")
    print()

    for attempt in range(MAX_RECOVERY_BACKS):

        print(
            f"→ Recuperación BACK "
            f"{attempt + 1}/{MAX_RECOVERY_BACKS}"
        )

        keycode_back()

        time.sleep(RECOVERY_BACK_DELAY)

        screen = screenshot()

        state, confidence, position = detect_state(
            screen,
            templates
        )

        print(
            f"RECOVERY ESTADO: {state} "
            f"| confianza: {confidence:.3f}"
        )

        if state == "RECOVER_COMPASS":

            print(
                "✓ Estado RECOVER_COMPASS detectado."
            )
            print(
                "→ Restaurando brújula..."
            )

            tap(
                COMPASS_X,
                COMPASS_Y
            )

            time.sleep(AFTER_COMPASS_DELAY)

            return "RECOVERED"

        if state != "UNKNOWN":

            print(
                "✓ Estado conocido recuperado."
            )

            return "RECOVERED"

    print()
    print("==========================")
    print(" ✗ RECUPERACIÓN FALLIDA")
    print("==========================")
    print(
        "No se logró volver a un estado conocido "
        "con BACK."
    )

    cv2.imwrite(
        "debug_recovery_failed.png",
        screen
    )

    print(
        "Captura guardada como debug_recovery_failed.png"
    )

    return "FAILED"


# ============================================================
# MOVIMIENTO DEL MAPA - BÚSQUEDA EN ESPIRAL
# ============================================================

def generate_spiral_movements(max_moves):
    """
    Genera una secuencia de movimientos en espiral:

        RIGHT x1
        DOWN  x1
        LEFT  x2
        UP    x2
        RIGHT x3
        DOWN  x3
        LEFT  x4
        UP    x4
        ...

    Importante:
    estas direcciones representan hacia dónde queremos
    desplazar la cámara.

    El gesto del dedo es contrario al desplazamiento
    visual del mapa.
    """

    movements = []

    directions = [
        "RIGHT",
        "DOWN",
        "LEFT",
        "UP"
    ]

    direction_index = 0
    steps_in_direction = 1

    while len(movements) < max_moves:

        # Dos direcciones consecutivas utilizan
        # la misma cantidad de pasos.
        for _ in range(2):

            direction = directions[
                direction_index % 4
            ]

            for _ in range(steps_in_direction):

                movements.append(direction)

                if len(movements) >= max_moves:
                    return movements

            direction_index += 1

        # Después de dos direcciones aumentamos
        # el tamaño de la espiral.
        steps_in_direction += 1

    return movements


SPIRAL_MOVEMENTS = generate_spiral_movements(
    MAX_MOVES
)

def move_map(direction):
    duration = 300

    if direction == "RIGHT":
        swipe(1100, 520, 650, 520, duration)

    elif direction == "LEFT":
        swipe(650, 520, 1100, 520, duration)

    elif direction == "DOWN":
        swipe(920, 740, 920, 230, duration)

    elif direction == "UP":
        swipe(920, 230, 920, 740, duration)

def open_search():
    """
    Abre el buscador. Si FARM_EVENT está activo, entra a Events
    y selecciona el evento configurado en EVENT_NUMBER.

    El nivel NO se modifica. Se utiliza el último nivel
    seleccionado manualmente por el usuario.
    """

    print()
    print("==========================")
    print(" ABRIENDO BUSCADOR")
    print("==========================")

    # --------------------------------------------------------
    # VALIDAR EVENTO
    # --------------------------------------------------------

    if FARM_EVENT and (
        EVENT_NUMBER < 1
        or EVENT_NUMBER > 4
    ):
        raise ValueError(
            "Por ahora EVENT_NUMBER debe estar entre 1 y 4."
        )

    # --------------------------------------------------------
    # ABRIR BRÚJULA
    # --------------------------------------------------------

    print("→ Abriendo brújula...")

    tap(
        COMPASS_X,
        COMPASS_Y
    )

    time.sleep(AFTER_COMPASS_DELAY)

    if FARM_EVENT:

        # ----------------------------------------------------
        # ABRIR EVENTS
        # ----------------------------------------------------

        print("→ Abriendo Events...")

        tap(EVENTS_X, EVENTS_Y)

        time.sleep(AFTER_EVENTS_DELAY)

        # ----------------------------------------------------
        # SELECCIONAR EVENTO
        # ----------------------------------------------------
        if EVENT_NUMBER == 4:
            print ("Evento 4 seleccionado_ desplazando evento")
            swipe (EVENT_SCROLL_X, EVENT_SCROLL_START_Y, EVENT_SCROLL_X, EVENT_SCROLL_END_Y, 500)
            time.sleep(AFTER_EVENT_SCROLL_DELAY)

            #despues del scroll visualiza la posicion del evento3
            event_y = EVENT_FIRST_Y + (2 * EVENT_SPACING_Y)
        else:
            event_y= (EVENT_FIRST_Y + (EVENT_NUMBER -1) * EVENT_SPACING_Y)
        print(f"->seleccionado evento {EVENT_NUMBER}")

        tap(EVENT_X, event_y)
        time.sleep(AFTER_EVENT_SELECT_DELAY)
    else:

        print(
            "→ FARM_EVENT desactivado. "
            "Saltando selección de Events."
        )


    # --------------------------------------------------------
    # SEARCH
    # --------------------------------------------------------

    print("→ Iniciando búsqueda...")

    tap(
        SEARCH_X,
        SEARCH_Y
    )

    time.sleep(AFTER_SEARCH_DELAY)

    print("✓ Buscador iniciado.")
    print()

# ============================================================
# BOT
# ============================================================

def run_bot():

    print()
    print("==========================")
    print(" GOTC SEARCH BOT")
    print("==========================")
    print()

    print("Cargando templates...")

    templates = load_templates()

    attack_template = load_template(
        ATTACK_TEMPLATE
    )

    march_template = load_template(
        MARCH_TEMPLATE
    )
    
    no_march_template = load_template(
        NO_MARCH_TEMPLATE
    )
    
    stop_template = load_template(
        STOP_TEMPLATE
    )

    print("Templates cargados.")
    print()
    
    moves = 0

    # Momento en el que comenzó un UNKNOWN.
    # None significa que no estamos en UNKNOWN.
    unknown_since = None

    try:

        while True:

            # --------------------------------------------
            # CAPTURAR
            # --------------------------------------------

            screen = screenshot()

            # --------------------------------------------
            # ANALIZAR
            # --------------------------------------------

            state, confidence, position = detect_state(
                screen,
                templates
            )

            print(
                f"ESTADO: {state} "
                f"| confianza: {confidence:.3f}"
            )

            # Si reconocimos algo, cualquier UNKNOWN
            # anterior queda resuelto.
            if state != "UNKNOWN":
                unknown_since = None

            # ============================================
            # IDLE / MAPA NORMAL
            # ============================================

            if state == "IDLE":

                print()
                print("==========================")
                print(" MAPA NORMAL DETECTADO")
                print("==========================")

                print(
                    "→ No hay una búsqueda activa. "
                    "Abriendo buscador..."
                )

                moves = 0
                unknown_since = None

                open_search()

                continue

            # ============================================
            # GO TO
            # ============================================

            if state == "GO_TO":

                print(
                    "✓ Criatura encontrada "
                    "fuera de pantalla."
                )

                tap(*position)

                print(
                    "  → Esperando movimiento "
                    "de cámara..."
                )

                time.sleep(AFTER_GO_TO_DELAY)

                # La cámara ya centró al enemigo.
                # Ahora realizar un ataque completo.
                
                result = attack_enemy_until_complete(
                    attack_template,
                    march_template,
                    no_march_template,
                    stop_template
                )
                
                if result == "STOP":

                    print()
                    print("==========================")
                    print(" FIN DE LA SESIÓN")
                    print("==========================")
                    print(
                        "Stamina agotada. "
                        "No se realizarán más búsquedas."
                    )

                    break

                if result == "COMPLETE":

                    print(
                        f"✓ Los {attacks_per_enemy()} ataques "
                        f"fueron completados."
                    )

                    print()
                    print("==========================")
                    print(" BUSCANDO SIGUIENTE OBJETIVO")
                    print("==========================")

                    moves = 0
                    unknown_since = None

                    open_search()

                    continue


                if result == "RECOVER":

                    print(
                        "→ Volviendo a analizar la pantalla..."
                    )

                    # No hacemos tap.
                    # No abrimos Search.
                    # Simplemente dejamos que el while principal
                    # tome otra captura y determine dónde estamos.
                    unknown_since = None

                    time.sleep(1.0)

                    continue


            # ============================================
            # NEXT
            # ============================================

            if state == "NEXT":

                print(
                    "✓ Criatura encontrada "
                    "en pantalla."
                )

                # Pulsar NEXT para centrar la criatura.
                tap(*position)

                print(
                    "  → Esperando movimiento "
                    "de cámara..."
                )

                time.sleep(AFTER_GO_TO_DELAY)

                # La criatura ya está centrada.
                # Comenzar los ataques al mismo objetivo.
                result = attack_enemy_until_complete(
                    attack_template,
                    march_template,
                    no_march_template,
                    stop_template
                )

                if result == "STOP":

                    print()
                    print("==========================")
                    print(" FIN DE LA SESIÓN")
                    print("==========================")
                    print(
                        "Stamina agotada. "
                        "No se realizarán más búsquedas."
                    )

                    break

                if result == "COMPLETE":

                    print(
                        f"✓ Los {attacks_per_enemy()} ataques "
                        f"fueron completados."
                    )

                    print()
                    print("==========================")
                    print(" BUSCANDO SIGUIENTE OBJETIVO")
                    print("==========================")

                    moves = 0
                    unknown_since = None

                    open_search()

                    continue

                if result == "RECOVER":

                    print(
                        "→ Volviendo a analizar la pantalla..."
                    )

                    unknown_since = None

                    time.sleep(1.0)

                    continue

            # ============================================
            # MOVE CAMERA
            # ============================================

            if state == "MOVE_CAMERA":

                if moves >= MAX_MOVES:

                    print()
                    print("==========================")
                    print(" ✗ BÚSQUEDA CANCELADA")
                    print("==========================")
                    print()
                    print(
                        f"Se alcanzó el máximo de "
                        f"{MAX_MOVES} movimientos."
                    )

                    cv2.imwrite(
                        "debug_max_moves.png",
                        screen
                    )

                    break

                print(
                    f"○ No hay objetivo aquí."
                )

                direction = SPIRAL_MOVEMENTS[moves]

                print(
                    f"  Moviendo mapa "
                    f"({moves + 1}/{MAX_MOVES}) "
                    f"→ {direction}"
                )

                move_map(direction)

                moves += 1

                # Darle un pequeño tiempo al juego para comenzar
                # a procesar el movimiento.
                time.sleep(AFTER_SWIPE_DELAY)

                # Después del swipe probablemente veremos
                # UNKNOWN durante unos instantes.
                # Eso es completamente normal.
                continue

            # ============================================
            # RECOVER COMPASS
            # ============================================

            if state == "RECOVER_COMPASS":

                print()
                print("==========================")
                print(" RECOVER_COMPASS DETECTADO")
                print("==========================")
                print(
                    "→ Pulsando posición de brújula "
                    "para restaurar mapa normal..."
                )

                tap(
                    COMPASS_X,
                    COMPASS_Y
                )

                time.sleep(AFTER_COMPASS_DELAY)

                moves = 0
                unknown_since = None

                continue

            # ============================================
            # UNKNOWN
            # ============================================

            if state == "UNKNOWN":

                # Primera captura UNKNOWN
                if unknown_since is None:

                    unknown_since = time.time()

                    print(
                        "… Estado transitorio detectado."
                    )

                elapsed = (
                    time.time() - unknown_since
                )

                print(
                    f"  Esperando al juego... "
                    f"{elapsed:.1f}/"
                    f"{MAX_UNKNOWN_SECONDS:.1f}s"
                )

                # ----------------------------------------
                # UNKNOWN demasiado largo
                # ----------------------------------------

                if elapsed >= MAX_UNKNOWN_SECONDS:

                    print()
                    print("==========================")
                    print(" ⚠ ESTADO DESCONOCIDO")
                    print("==========================")
                    print()

                    print(
                        "El juego permaneció en UNKNOWN "
                        "demasiado tiempo."
                    )

                    print(
                        "Se intentará recuperación automática."
                    )

                    cv2.imwrite(
                        "debug_unknown.png",
                        screen
                    )

                    print()
                    print(
                        "Captura guardada como:"
                    )

                    print(
                        "debug_unknown.png"
                    )

                    recovery_result = recover_from_unknown(
                        templates
                    )

                    if recovery_result == "RECOVERED":

                        moves = 0
                        unknown_since = None

                        print(
                            "→ Volviendo a analizar pantalla..."
                        )

                        continue

                    break

                # ----------------------------------------
                # Esperar y volver a observar
                # ----------------------------------------

                time.sleep(
                    UNKNOWN_POLL_INTERVAL
                )

                continue

    except KeyboardInterrupt:

        print()
        print("==========================")
        print(" BOT DETENIDO")
        print("==========================")
        print()
        print(
            "Detenido manualmente con CTRL+C."
        )



def main():
    send_ntfy_notification(
        "GOTC bot iniciado",
        "El bot GOTC acaba de iniciar."
    )

    try:
        run_bot()

    finally:
        send_ntfy_notification(
            "GOTC bot detenido",
            "El bot GOTC se detuvo."
        )


# ============================================================
# INICIO
# ============================================================

if __name__ == "__main__":
    main()
