import subprocess
import time

import cv2
import numpy as np


PNG_SIGNATURE = b"\x89PNG\r\n\x1a\n"

THRESHOLD = 0.85

TEMPLATES = {
    "GO_TO": "go_to.png",
    "NEXT": "next.png",
    "MOVE_CAMERA": "move_camera.png",
}


def screenshot():
    """Obtiene directamente una captura de Waydroid mediante ADB."""

    result = subprocess.run(
        ["adb", "exec-out", "screencap", "-p"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )

    data = result.stdout

    # Waydroid añade un warning de amdgpu antes del PNG.
    start = data.find(PNG_SIGNATURE)

    if start == -1:
        raise RuntimeError("ADB no devolvió una imagen PNG")

    data = data[start:]

    array = np.frombuffer(data, dtype=np.uint8)
    image = cv2.imdecode(array, cv2.IMREAD_COLOR)

    if image is None:
        raise RuntimeError("OpenCV no pudo decodificar la captura")

    return image


def load_templates():
    templates = {}

    for name, filename in TEMPLATES.items():

        image = cv2.imread(filename)

        if image is None:
            raise RuntimeError(
                f"No pude cargar el template: {filename}"
            )

        templates[name] = image

    return templates


def find_template(screen, template):

    result = cv2.matchTemplate(
        screen,
        template,
        cv2.TM_CCOEFF_NORMED
    )

    _, confidence, _, location = cv2.minMaxLoc(result)

    h, w = template.shape[:2]

    center = (
        location[0] + w // 2,
        location[1] + h // 2
    )

    return confidence, center


def detect_state(screen, templates):

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

    # Mostrar todas las puntuaciones para calibrar
    print(
        " | ".join(
            f"{name}: {data['confidence']:.3f}"
            for name, data in results.items()
        )
    )

    # Nos quedamos con la coincidencia más fuerte
    best_name = max(
        results,
        key=lambda name: results[name]["confidence"]
    )

    best = results[best_name]

    if best["confidence"] >= THRESHOLD:

        return (
            best_name,
            best["confidence"],
            best["position"]
        )

    return (
        "UNKNOWN",
        best["confidence"],
        best["position"]
    )


def main():

    print("Cargando templates...")

    templates = load_templates()

    print("Templates cargados.")
    print()
    print("Detector GOTC iniciado.")
    print("CTRL+C para detener.")
    print()

    try:

        while True:

            screen = screenshot()

            state, confidence, position = detect_state(
                screen,
                templates
            )

            print(
                f"ESTADO: {state} "
                f"| confianza={confidence:.3f} "
                f"| posición={position}"
            )

            print("-" * 60)

            time.sleep(1)

    except KeyboardInterrupt:

        print()
        print("Detector detenido.")


if __name__ == "__main__":
    main()
