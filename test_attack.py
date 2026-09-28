import subprocess
import cv2
import numpy as np

PNG_SIGNATURE = b"\x89PNG\r\n\x1a\n"

ATTACK_TEMPLATE = "attack.png"
ATTACK_THRESHOLD = 0.90

MARCH_TEMPLATE = "march.png"
MARCH_THRESHOLD = 0.90


def screenshot():
    result = subprocess.run(
        ["adb", "exec-out", "screencap", "-p"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )

    data = result.stdout
    start = data.find(PNG_SIGNATURE)

    if start == -1:
        raise RuntimeError("No se encontró un PNG válido.")

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
            "No se pudo decodificar la captura."
        )

    return image


def find_template(screen, filename):
    template = cv2.imread(filename)

    if template is None:
        raise RuntimeError(
            f"No pude cargar {filename}"
        )

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


def main():
    screen = screenshot()

    # ==========================================
    # ATTACK
    # ==========================================

    attack_confidence, attack_position = find_template(
        screen,
        ATTACK_TEMPLATE
    )

    print()
    print(
        f"ATTACK confianza: "
        f"{attack_confidence:.3f}"
    )

    print(
        f"ATTACK posición: "
        f"{attack_position}"
    )

    if attack_confidence >= ATTACK_THRESHOLD:
        print("✓ ATTACK DETECTADO")
    else:
        print("✗ ATTACK NO DETECTADO")

    # ==========================================
    # MARCH
    # ==========================================

    march_confidence, march_position = find_template(
        screen,
        MARCH_TEMPLATE
    )

    print()
    print(
        f"MARCH confianza: "
        f"{march_confidence:.3f}"
    )

    print(
        f"MARCH posición: "
        f"{march_position}"
    )

    if march_confidence >= MARCH_THRESHOLD:
        print("✓ MARCH DETECTADO")
    else:
        print("✗ MARCH NO DETECTADO")

    print()


if __name__ == "__main__":
    main()
