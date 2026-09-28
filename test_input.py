import subprocess
import time


def tap(x, y):
    print(f"Tap ({x}, {y})")
    subprocess.run(
        ["adb", "shell", "input", "tap", str(x), str(y)],
        check=True
    )


print("Comenzando en 3 segundos...")
time.sleep(3)

# 1. Brújula
tap(693, 837)
time.sleep(2)

# 2. Events
tap(1000, 300)
time.sleep(2)

print("Prueba terminada.")
