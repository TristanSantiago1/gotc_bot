import subprocess
import cv2
import numpy as np

PNG_SIGNATURE = b"\x89PNG\r\n\x1a\n"


def screenshot():
    result = subprocess.run(
        ["adb", "exec-out", "screencap", "-p"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )

    data = result.stdout

    # Waydroid está introduciendo un warning antes del PNG.
    # Buscamos dónde comienza realmente la imagen.
    start = data.find(PNG_SIGNATURE)

    if start == -1:
        raise RuntimeError(
            "No se encontró un PNG en la salida de ADB.\n"
            f"STDERR: {result.stderr.decode(errors='replace')}"
        )

    data = data[start:]

    image_array = np.frombuffer(data, dtype=np.uint8)
    image = cv2.imdecode(image_array, cv2.IMREAD_COLOR)

    if image is None:
        raise RuntimeError("OpenCV no pudo decodificar la captura.")

    return image


print("Capturando GOTC...")

img = screenshot()

height, width = img.shape[:2]

print(f"Captura correcta: {width}x{height}")

cv2.imwrite("screenshot.png", img)

print("Guardada como screenshot.png")
