# GOTC Farming Bot --- Documentación técnica

## 1. Descripción

Este proyecto automatiza parte del proceso de farmeo de criaturas en
**Game of Thrones: Conquest (GOTC)** ejecutado dentro de **Waydroid** en
Linux.

El bot utiliza **ADB** para interactuar con Android y **OpenCV** para
reconocer elementos de la interfaz mediante *template matching*. En
lugar de depender únicamente de tiempos y coordenadas fijas, observa la
pantalla y determina el estado actual del juego antes de continuar.

El flujo implementado actualmente permite:

1.  Detectar si GOTC se encuentra en el mapa sin una búsqueda activa.
2.  Abrir la brújula.
3.  Entrar en la sección **Events**.
4.  Seleccionar un evento configurable según su posición de arriba hacia
    abajo.
5.  Conservar el último nivel de criatura seleccionado manualmente.
6.  Pulsar **Search**.
7.  Detectar si:
    -   se encontró una criatura fuera de pantalla (`GO_TO`);
    -   se encontró una criatura visible (`NEXT`);
    -   es necesario mover la cámara (`MOVE_CAMERA`);
    -   el juego está en el mapa sin búsqueda (`IDLE`);
    -   no se reconoce un estado (`UNKNOWN`).
8.  Mover el mapa siguiendo un patrón en espiral hasta encontrar una
    criatura.
9.  Centrar la criatura.
10. Seleccionarla y detectar el botón **ATTACK**.
11. Detectar y pulsar **MARCH**.
12. Repetir una cantidad configurable de ataques contra la misma
    criatura.
13. Esperar y reintentar si no existen marchas disponibles.
14. Recuperarse de determinados fallos producidos por lag.
15. Volver a buscar automáticamente otra criatura al completar el
    objetivo.
16. Detener completamente la sesión cuando se detecta la pantalla de
    recarga de stamina (`stop.png`).

------------------------------------------------------------------------

## 2. Ambiente utilizado

El bot fue desarrollado y probado con el siguiente ambiente:

-   **Sistema operativo:** Ubuntu 24.04.3 LTS
-   **CPU:** AMD Ryzen 3 PRO 2200G con Radeon Vega Graphics
-   **CPU virtualización:** AMD-V / SVM habilitado
-   **RAM:** aproximadamente 6 GB
-   **Swap:** aproximadamente 15 GB
-   **Sesión gráfica:** Wayland
-   **Android:** Waydroid
-   **Imagen de Waydroid:** GAPPS
-   **Traducción ARM:** `libndk`, necesaria para ejecutar GOTC en el
    equipo AMD/x86-64 utilizado
-   **Resolución observada mediante ADB:** 1840 × 1048
-   **Python:** Python 3
-   **Automatización Android:** ADB
-   **Visión artificial:** OpenCV
-   **Procesamiento numérico:** NumPy

> Las coordenadas y templates documentados en este proyecto están
> calibrados para este ambiente. Cambiar resolución, densidad, escala o
> distribución de la interfaz puede requerir recalibrarlos.

------------------------------------------------------------------------

## 3. Arquitectura general

El sistema se puede representar así:

``` text
Linux / Python
      │
      ├── ADB
      │    ├── screencap
      │    ├── tap
      │    └── swipe
      │
      ▼
   Waydroid
      │
      ▼
Game of Thrones: Conquest
      ▲
      │
 OpenCV / templates
```

Python controla el flujo. ADB obtiene capturas y envía entradas
táctiles. OpenCV compara las capturas con imágenes de referencia para
decidir qué debe hacer el bot.

------------------------------------------------------------------------

## 4. Instalación base

### 4.1. Comprobar virtualización

Waydroid necesita un ambiente Linux compatible. En el equipo utilizado
se verificó AMD-V/KVM.

Puede comprobarse KVM con:

``` bash
kvm-ok
```

Si el comando no existe:

``` bash
sudo apt update
sudo apt install cpu-checker
```

El resultado esperado es que KVM pueda utilizarse.

### 4.2. Instalar Waydroid

Instalar Waydroid siguiendo el procedimiento correspondiente a Ubuntu y
configurar una imagen con GAPPS.

Una vez instalado, comprobar:

``` bash
waydroid status
```

El objetivo es disponer de un Android funcional donde GOTC pueda
ejecutarse correctamente.

### 4.3. Compatibilidad ARM

GOTC necesita compatibilidad con binarios ARM en el equipo x86-64
utilizado.

En este proyecto se utilizó:

-   `casualsnek/waydroid_script`
-   traducción ARM `libndk`

Después de instalarla, GOTC pudo iniciarse y ejecutarse correctamente
dentro de Waydroid.

> Esta parte depende de la versión de Waydroid y del script de
> compatibilidad utilizado. Conviene seguir las instrucciones de la
> versión actual de `waydroid_script` en vez de conservar comandos
> antiguos del instalador.

### 4.4. Instalar ADB

``` bash
sudo apt update
sudo apt install adb
```

Comprobar:

``` bash
adb devices
```

Después verificar que ADB puede interactuar con Waydroid.

Una prueba simple:

``` bash
adb shell input tap 920 500
```

------------------------------------------------------------------------

## 5. Crear el proyecto Python

El proyecto utilizado se encuentra en:

``` text
~/gotc-bot
```

Crear la carpeta:

``` bash
mkdir -p ~/gotc-bot
cd ~/gotc-bot
```

Crear un entorno virtual:

``` bash
python3 -m venv venv
```

Activarlo:

``` bash
source venv/bin/activate
```

Actualizar `pip`:

``` bash
python -m pip install --upgrade pip
```

Instalar dependencias:

``` bash
pip install opencv-python numpy
```

Cada vez que se abra una terminal nueva:

``` bash
cd ~/gotc-bot
source venv/bin/activate
```

------------------------------------------------------------------------

## 6. Archivos principales

Una estructura aproximada del proyecto es:

``` text
gotc-bot/
├── search_bot.py
├── test_attack.py
├── test_capture.py
├── test_input.py
├── vision.py
├── go_to.png
├── next.png
├── move_camera.png
├── idle.png
├── attack.png
├── march.png
├── no_march.png
├── stop.png
└── venv/
```

Los scripts de prueba no son obligatorios para ejecutar el bot final,
pero son útiles para recalibrar o diagnosticar problemas.

------------------------------------------------------------------------

## 7. Templates de reconocimiento

El bot utiliza imágenes PNG pequeñas recortadas directamente de GOTC.

### `idle.png`

Representa la brújula visible en el mapa normal.

Se utiliza para detectar que no existe una búsqueda activa y que el bot
debe iniciar una nueva.

### `go_to.png`

Representa el botón **Go To**.

Significa que GOTC encontró una criatura, pero se encuentra fuera de la
zona actualmente visible.

### `next.png`

Representa el botón **Next**.

Indica que el buscador encontró una criatura en el estado
correspondiente y permite centrarla.

### `move_camera.png`

Representa el mensaje:

``` text
Move camera to continue search.
```

Cuando aparece, el bot mueve el mapa y vuelve a comprobar el estado.

### `attack.png`

Representa el botón **ATTACK** que aparece al seleccionar una criatura.

En las pruebas realizadas alcanzó una confianza de `1.000`.

### `march.png`

Representa la parte estable del botón **MARCH**.

No debe incluir el tiempo dinámico mostrado debajo del botón, por
ejemplo `55s`.

En las pruebas también alcanzó una confianza de `1.000`.

### `no_march.png`

Representa una parte estable de:

``` text
ADD MARCH SLOTS
```

Se recomienda utilizar el título y no el botón `GO TO`, ya que este
último podría confundirse con el `GO_TO` del buscador.

Cuando se detecta, el bot pulsa **Cancel**, espera y vuelve a intentar
el mismo ataque sin incrementar el contador.

### `stop.png`

Representa una parte estable y exclusiva de la pantalla de recarga que
aparece cuando no existe stamina suficiente para continuar.

Cuando se detecta:

``` text
STOP
→ stamina insuficiente
→ detener completamente el bot
```

No se realizan nuevas búsquedas ni ataques.

------------------------------------------------------------------------

## 8. Recomendaciones para crear templates

Los templates deben:

-   estar recortados alrededor de elementos estables;
-   evitar números, temporizadores o textos variables;
-   evitar zonas animadas;
-   tener el mismo tamaño y escala con los que aparecerán durante la
    ejecución;
-   ser suficientemente exclusivos para no coincidir con otros
    elementos.

El reconocimiento utiliza:

``` python
cv2.matchTemplate(
    screen,
    template,
    cv2.TM_CCOEFF_NORMED
)
```

y posteriormente:

``` python
cv2.minMaxLoc(result)
```

El valor obtenido se compara contra un umbral de confianza.

Ejemplo:

``` python
if confidence >= 0.90:
    # Template detectado
```

------------------------------------------------------------------------

## 9. Capturas de pantalla

Waydroid produjo en este equipo un warning antes de los bytes reales del
PNG al utilizar:

``` bash
adb exec-out screencap -p
```

Por eso el código no intenta decodificar directamente toda la salida.
Primero localiza la firma PNG:

``` python
PNG_SIGNATURE = b"\x89PNG\r\n\x1a\n"
```

Después elimina cualquier contenido anterior:

``` python
start = data.find(PNG_SIGNATURE)
data = data[start:]
```

Finalmente OpenCV decodifica la captura:

``` python
image_array = np.frombuffer(data, dtype=np.uint8)
image = cv2.imdecode(image_array, cv2.IMREAD_COLOR)
```

Esto hace que el bot tolere el warning observado en Waydroid.

------------------------------------------------------------------------

## 10. Interacción mediante ADB

Las acciones principales se encapsulan en funciones.

### Tap

Conceptualmente:

``` python
adb shell input tap X Y
```

Ejemplo:

``` python
tap(920, 500)
```

### Swipe

Conceptualmente:

``` python
adb shell input swipe X1 Y1 X2 Y2 DURACION
```

El bot lo utiliza principalmente para mover el mapa durante la búsqueda.

------------------------------------------------------------------------

## 11. Configuración del evento

El evento se selecciona por posición vertical.

El área observada de eventos comienza aproximadamente en `Y=346` y
termina alrededor de `Y=840`.

Mediciones:

``` text
Evento 1: Y=355 a Y=500
Evento 2: Y=520 a Y=666
```

De ellas se obtuvo aproximadamente:

``` text
Altura del evento:     145 px
Separación:             20 px
Paso vertical total:   165 px
```

Centros utilizados:

``` text
Evento 1 → Y ≈ 428
Evento 2 → Y ≈ 593
Evento 3 → Y ≈ 758
```

La fórmula es:

``` python
event_y = EVENT_FIRST_Y + (EVENT_NUMBER - 1) * EVENT_SPACING_Y
```

con:

``` python
EVENT_FIRST_Y = 428
EVENT_SPACING_Y = 165
```

Por tanto basta cambiar:

``` python
EVENT_NUMBER = 1
```

por `2`, `3` o `4`.

Actualmente se contemplan los primeros tres eventos visibles de forma
directa. Para `EVENT_NUMBER = 4`, el bot hace un scroll vertical en la
lista de eventos y después pulsa la posición donde queda visible el
cuarto evento.

El código valida que:

``` python
1 <= EVENT_NUMBER <= 4
```

------------------------------------------------------------------------

## 12. Coordenadas principales

Las coordenadas utilizadas en el ambiente de desarrollo incluyen:

``` python
COMPASS_X = 693
COMPASS_Y = 837

EVENTS_X = 1000
EVENTS_Y = 300

SEARCH_X = 1000
SEARCH_Y = 800

EVENT_X = 920
EVENT_FIRST_Y = 428
EVENT_SPACING_Y = 165

EVENT_SCROLL_X = 920
EVENT_SCROLL_START_Y = 750
EVENT_SCROLL_END_Y = 450
AFTER_EVENT_SCROLL_DELAY = 1.0
```

Para seleccionar la criatura se utilizan dos alturas distintas:

``` python
TARGET_X = 920
TARGET_Y_FIRST = 320
TARGET_Y_REPEAT = 520
```

La razón es que el primer ataque se realiza justo después de
`GO_TO`/`NEXT`, mientras que los ataques posteriores pueden requerir
otra posición vertical para seleccionar de forma fiable la misma
criatura.

> En pruebas posteriores del proyecto se ajustaron coordenadas de
> selección para mejorar la fiabilidad. Si la interfaz cambia, deben
> recalibrarse con capturas reales.

------------------------------------------------------------------------

## 13. Configuraciones principales del bot

Ejemplo conceptual de configuración:

``` python
FARM_EVENT = True
ELITE_CREATURE = False

ATTACKS_PER_ENEMY = 5
EVENT_NUMBER = 1

MAX_MOVES = 40
MAX_UNKNOWN_SECONDS = 15.0

UNKNOWN_POLL_INTERVAL = 0.5
AFTER_SWIPE_DELAY = 0.5
AFTER_GO_TO_DELAY = 3.0

ATTACK_THRESHOLD = 0.90
MARCH_THRESHOLD = 0.856
NO_MARCH_THRESHOLD = 0.90
STOP_THRESHOLD = 0.90

MARCH_RETRY_DELAY = 20.0
```

### `ATTACKS_PER_ENEMY`

Número exacto de ataques enviados a cada criatura cuando
`FARM_EVENT = True`.

El contador solo aumenta después de confirmar correctamente **MARCH**.

### `FARM_EVENT`

Define el modo de búsqueda:

``` text
True  = buscar desde Events y atacar ATTACKS_PER_ENEMY veces
False = usar búsqueda directa
```

Cuando `FARM_EVENT = False`, el número de ataques ya no sale de
`ATTACKS_PER_ENEMY`; depende de `ELITE_CREATURE`.

### `ELITE_CREATURE`

Solo aplica cuando `FARM_EVENT = False`.

``` text
True  = criatura elite, 4 ataques exactos
False = criatura normal, 1 ataque exacto
```

Si `FARM_EVENT = True`, esta variable no cambia la cantidad de ataques:
se mantienen los ataques configurados por `ATTACKS_PER_ENEMY`.

### `EVENT_NUMBER`

Evento que se seleccionará:

``` text
1 = primer evento visible
2 = segundo evento visible
3 = tercer evento visible
4 = cuarto evento, usando scroll vertical
```

### Nivel de criatura

El bot actualmente **no selecciona automáticamente el nivel**.

Antes de iniciar la automatización se debe seleccionar manualmente el
nivel deseado. GOTC conserva la última selección y el bot la reutiliza.

### `MAX_MOVES`

Máximo de movimientos permitidos durante una búsqueda antes de
considerar que no se encontró un objetivo.

### `MARCH_RETRY_DELAY`

Tiempo de espera antes de volver a intentar un ataque cuando todas las
marchas están ocupadas.

------------------------------------------------------------------------

## 14. Estados del buscador

La función de detección puede reconocer:

``` text
IDLE
GO_TO
NEXT
MOVE_CAMERA
UNKNOWN
```

### IDLE

Mapa normal con brújula visible.

Acción:

``` text
IDLE
 ↓
Brújula
 ↓
Events
 ↓
evento configurado
 ↓
Search
```

### GO_TO

Existe una criatura encontrada fuera de pantalla.

Acción:

``` text
GO_TO
 ↓
tap Go To
 ↓
esperar movimiento de cámara
 ↓
seleccionar criatura
 ↓
ataques
```

### NEXT

Existe una criatura encontrada en el estado representado por `next.png`.

El bot pulsa `NEXT`, espera el movimiento de cámara y continúa al ciclo
de ataques.

### MOVE_CAMERA

No existe un objetivo utilizable en la posición actual.

El bot desplaza el mapa y vuelve a observar.

### UNKNOWN

Ningún template conocido supera su umbral.

Los estados `UNKNOWN` breves se consideran normales porque GOTC puede
tardar en actualizar la interfaz.

Si persiste demasiado tiempo se genera una captura de depuración.

------------------------------------------------------------------------

## 15. Búsqueda en espiral

Cuando GOTC solicita mover la cámara, el bot no desplaza el mapa
aleatoriamente.

Genera una secuencia:

``` text
RIGHT x1
DOWN  x1
LEFT  x2
UP    x2
RIGHT x3
DOWN  x3
LEFT  x4
UP    x4
...
```

Los swipes calibrados que funcionaron en el ambiente utilizado son:

``` python
RIGHT:
    swipe(1100, 520, 650, 520, 300)

LEFT:
    swipe(650, 520, 1100, 520, 300)

DOWN:
    swipe(920, 740, 920, 230, 300)

UP:
    swipe(920, 230, 920, 740, 300)
```

Se comprobó que iniciar algunos swipes demasiado hacia la derecha, por
ejemplo alrededor de `X=1150`, podía quedar fuera de la zona interactiva
real de GOTC. `X=1100` resultó fiable.

Después de cada swipe se vuelve a analizar la pantalla; no se realizan
múltiples movimientos a ciegas.

------------------------------------------------------------------------

## 16. Apertura automática del buscador

`open_search()` automatiza:

``` text
Mapa
 ↓
Brújula
 ↓
Events
 ↓
Evento N
 ↓
Search
```

No selecciona el nivel.

El evento se obtiene con:

``` python
event_y = (
    EVENT_FIRST_Y
    + (EVENT_NUMBER - 1) * EVENT_SPACING_Y
)
```

Esto evita mantener una coordenada independiente para cada evento
visible. En el caso de `EVENT_NUMBER = 4`, el bot primero desplaza la
lista con:

``` python
swipe(
    EVENT_SCROLL_X,
    EVENT_SCROLL_START_Y,
    EVENT_SCROLL_X,
    EVENT_SCROLL_END_Y,
    500
)
```

Después reutiliza la posición visual del tercer evento visible:

``` python
event_y = EVENT_FIRST_Y + (2 * EVENT_SPACING_Y)
```

------------------------------------------------------------------------

## 17. Ciclo de ataque

Antes de iniciar el ciclo, el bot calcula la cantidad exacta con
`attacks_per_enemy()`:

``` text
FARM_EVENT=True                         -> ATTACKS_PER_ENEMY
FARM_EVENT=False, ELITE_CREATURE=True   -> 4
FARM_EVENT=False, ELITE_CREATURE=False  -> 1
```

Después de centrar una criatura:

``` text
seleccionar objetivo
 ↓
detectar ATTACK
 ↓
tap ATTACK
 ↓
comprobar resultado
```

El resultado puede conducir a diferentes estados:

``` text
SENT
NO_MARCH
STOP
RECOVER
```

### SENT

Se encontró y pulsó correctamente **MARCH**.

Solo entonces:

``` python
attacks_done += 1
```

Esto evita contar intentos que realmente no salieron.

### NO_MARCH

Aparece `ADD MARCH SLOTS`.

El bot:

``` text
detecta no_march.png
 ↓
Cancel
 ↓
espera MARCH_RETRY_DELAY
 ↓
reintenta el mismo número de ataque
```

No incrementa `attacks_done`.

### STOP

Se detecta `stop.png`.

Significa que la stamina asignada a la sesión se terminó.

El bot detiene completamente la automatización.

### RECOVER

Algo esperado no apareció, normalmente debido a lag o a un tap que no
fue registrado correctamente.

En vez de finalizar inmediatamente, el control regresa a la máquina de
estados principal para volver a observar la interfaz.

------------------------------------------------------------------------

## 18. Recuperación ante lag

Un fallo observado fue:

``` text
→ Seleccionando objetivo...
ATTACK intento 1/10 | confianza: 0.216
...
ATTACK intento 10/10 | confianza: 0.223
✗ No apareció ATTACK
```

La causa puede ser que el juego todavía estuviera procesando el
movimiento de cámara y el tap de selección no surtiera efecto.

La versión robusta no debe interpretar automáticamente este caso como un
error fatal.

Devuelve:

``` text
RECOVER
```

y el controlador principal vuelve a ejecutar reconocimiento.

Puede encontrar:

``` text
IDLE        → iniciar una nueva búsqueda
GO_TO       → volver a centrar el objetivo
NEXT        → continuar con el objetivo
MOVE_CAMERA → continuar la búsqueda
UNKNOWN     → esperar
```

Esto reduce la dependencia de tiempos perfectos en un equipo con
recursos limitados.

------------------------------------------------------------------------

## 19. Gestión de marchas

El bot no necesita conocer exactamente cuántos slots de marcha existen.

Aunque durante el desarrollo había tres marchas disponibles, la interfaz
del juego es la fuente de verdad.

Ejemplo:

``` text
Ataque 1/5 → SENT
Ataque 2/5 → SENT
Ataque 3/5 → SENT

Ataque 4/5
 ↓
ADD MARCH SLOTS
 ↓
NO_MARCH
 ↓
esperar
 ↓
reintentar 4/5
```

Cuando una marcha regresa:

``` text
Ataque 4/5 → SENT
Ataque 5/5 → SENT
```

Esto permite que la lógica siga funcionando aunque posteriormente cambie
la cantidad de marchas disponibles.

------------------------------------------------------------------------

## 20. Criterio de parada por stamina

El usuario asigna previamente la stamina que desea utilizar durante la
sesión.

Cuando al intentar continuar aparece la pantalla de recarga, `stop.png`
permite reconocerla.

El comportamiento esperado es:

``` text
ATTACK
 ↓
pantalla de stamina
 ↓
STOP detectado
 ↓
no realizar más acciones
 ↓
finalizar sesión
```

El bot debe dejar la pantalla tal como está y no intentar cerrar la
ventana ni abrir una nueva búsqueda.

Ejemplo de salida:

``` text
==========================
 🛑 STAMINA AGOTADA
==========================
Se detectó la pantalla de recarga.

==========================
 FIN DE LA SESIÓN
==========================
Stamina agotada.
No se realizarán más búsquedas.
```

------------------------------------------------------------------------

## 21. Flujo completo

``` text
INICIO
  │
  ▼
capturar pantalla
  │
  ▼
detectar estado
  │
  ├── IDLE
  │     │
  │     ▼
  │   open_search()
  │
  ├── MOVE_CAMERA
  │     │
  │     ▼
  │   mover mapa
  │     │
  │     └──────────► volver a detectar
  │
  ├── GO_TO / NEXT
  │     │
  │     ▼
  │   centrar criatura
  │     │
  │     ▼
  │   ciclo de ataques
  │     │
  │     ├── SENT ─────► incrementar contador
  │     │
  │     ├── NO_MARCH ─► esperar y reintentar
  │     │
  │     ├── RECOVER ──► volver a detectar estado
  │     │
  │     └── STOP ─────► FIN
  │     │
  │     ▼
  │   ataques completados
  │     │
  │     ▼
  │   nueva búsqueda
  │
  └── UNKNOWN
        │
        ▼
      esperar
        │
        └──────────────► volver a detectar
```

------------------------------------------------------------------------

## 22. Preparación antes de ejecutar

Antes de iniciar una sesión:

1.  Iniciar Waydroid.
2.  Abrir GOTC.
3.  Entrar al mapa.
4.  Asegurarse de que la cuenta está en un estado normal para atacar.
5.  Seleccionar manualmente al menos una vez el nivel de criatura que se
    desea farmear.
6.  Configurar `FARM_EVENT`.
7.  Si `FARM_EVENT = True`, configurar `ATTACKS_PER_ENEMY` y
    `EVENT_NUMBER`.
8.  Si `FARM_EVENT = False`, configurar `ELITE_CREATURE`.
9.  Verificar que la stamina disponible sea la que se desea gastar.
10. Verificar que todos los templates PNG correspondan a la interfaz
    actual.
11. Activar el entorno virtual.

Ejecutar:

``` bash
cd ~/gotc-bot
source venv/bin/activate
python search_bot.py
```

Para detener manualmente:

``` text
Ctrl+C
```

------------------------------------------------------------------------

## 23. Diagnóstico

### ADB no responde

Comprobar:

``` bash
adb devices
```

y después:

``` bash
adb shell input tap 920 500
```

### No se puede obtener captura

Probar manualmente:

``` bash
adb shell screencap -p /sdcard/test.png
adb pull /sdcard/test.png ~/test.png
```

### Un template no se detecta

Revisar la confianza impresa:

``` text
ATTACK confianza: 0.xxx
```

Si es muy baja:

-   comprobar que la interfaz está realmente en el estado esperado;
-   recrear el template;
-   hacer un recorte más estable;
-   comprobar resolución y escala;
-   evitar contenido dinámico.

### UNKNOWN prolongado

El bot puede guardar:

``` text
debug_unknown.png
```

### ATTACK no encontrado

Puede guardar:

``` text
debug_attack_not_found.png
```

### MARCH no encontrado

Puede guardar:

``` text
debug_march_not_found.png
```

### Máximo de movimientos alcanzado

Puede guardar:

``` text
debug_max_moves.png
```

Estas capturas permiten observar exactamente en qué pantalla estaba GOTC
cuando falló la automatización.

------------------------------------------------------------------------

## 24. Consideraciones sobre resolución

La automatización combina reconocimiento visual con coordenadas
absolutas.

Por ello, coordenadas como:

``` text
(693, 837)
(1000, 300)
(1000, 800)
(920, 320)
(920, 520)
```

solo deben considerarse válidas para la configuración visual probada.

Si cambia:

-   resolución de Waydroid;
-   densidad Android;
-   tamaño de ventana;
-   relación de aspecto;
-   escala de interfaz de GOTC;

será necesario volver a validar coordenadas y posiblemente regenerar
templates.

------------------------------------------------------------------------

## 25. Limitaciones actuales

La versión actual tiene deliberadamente algunas simplificaciones:

-   El nivel de criatura se configura manualmente antes de iniciar.
-   La selección automática contempla los primeros cuatro eventos; el
    cuarto usa scroll vertical.
-   Eventos posteriores al cuarto todavía requerirían ampliar la lógica
    de scroll.
-   Los taps principales siguen utilizando coordenadas absolutas.
-   La detección visual depende de que los templates correspondan a la
    interfaz actual.
-   Las esperas están calibradas para el rendimiento del equipo
    utilizado.
-   La recuperación automática cubre estados conocidos, pero una
    pantalla completamente nueva puede terminar en `UNKNOWN`.

------------------------------------------------------------------------

## 26. Posibles mejoras futuras

Algunas extensiones naturales del proyecto son:

-   selección automática del nivel;
-   soporte para eventos posteriores al cuarto mediante scroll
    repetido;
-   unificar la lógica repetida de `GO_TO` y `NEXT`;
-   centralizar el resultado del ataque en una única función de
    observación;
-   detectar `STOP`, `NO_MARCH` y `MARCH` simultáneamente durante una
    ventana de tiempo;
-   reemplazar más coordenadas absolutas por detección visual;
-   archivo externo de configuración (`config.json`, TOML o YAML);
-   estadísticas de sesión;
-   contador total de criaturas;
-   contador total de ataques;
-   duración de sesión;
-   registro a archivo;
-   capturas automáticas ante errores;
-   reintentos configurables;
-   interfaz sencilla para modificar evento, ataques y tiempos sin
    editar Python.

------------------------------------------------------------------------

## 27. Resumen técnico del código

El código puede dividirse conceptualmente en estos módulos:

``` text
CONFIGURACIÓN
    │
    ├── templates
    ├── thresholds
    ├── coordenadas
    ├── delays
    └── parámetros de farming

ADB
    │
    ├── adb()
    ├── tap()
    └── swipe()

CAPTURA
    │
    └── screenshot()

VISIÓN
    │
    ├── load_templates()
    ├── load_template()
    ├── find_template()
    └── detect_state()

NAVEGACIÓN
    │
    ├── open_search()
    ├── generate_spiral_movements()
    └── move_map()

ATAQUE
    │
    ├── check_stop()
    ├── check_no_march()
    ├── confirm_march()
    ├── attack_target()
    └── attack_enemy_until_complete()

CONTROL
    │
    └── main()
```

`main()` funciona como la máquina de estados principal y coordina el
resto de componentes.

------------------------------------------------------------------------

## 28. Estado actual del proyecto

Al momento de esta documentación se ha comprobado funcionalmente:

-   apertura automática de la brújula;
-   acceso a Events;
-   selección de eventos 1, 2, 3 y 4 mediante configuración;
-   cálculo de posiciones para los tres eventos visibles;
-   scroll vertical para seleccionar el cuarto evento;
-   búsqueda de criaturas;
-   búsqueda en espiral;
-   detección de `GO_TO`;
-   detección de `NEXT`;
-   detección de `MOVE_CAMERA`;
-   detección de mapa normal mediante `IDLE`;
-   selección del objetivo;
-   detección de `ATTACK`;
-   detección de `MARCH`;
-   envío de múltiples ataques;
-   contador exacto de ataques enviados;
-   espera cuando no hay marchas;
-   recuperación ante ciertos fallos causados por lag;
-   repetición automática con una nueva criatura;
-   criterio de parada por falta de stamina mediante `stop.png`.

El proyecto se encuentra, por tanto, en una etapa de **farming
automático funcional con recuperación básica y criterio de parada**,
quedando como mejoras futuras principalmente la robustez, configuración
externa y automatización de más opciones de la interfaz.
