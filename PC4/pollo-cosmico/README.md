# Persona 1 — Core, Física/Colisiones y Build

Este paquete ya está probado y corre. Contiene todo lo que le toca a Persona 1
según el reparto de trabajo del equipo.

## Cómo correrlo

(Atención) Si tienes una versión de python mayor a la de 3.13 es posible que genere conflictos con pygame.
Esto se debe a que para versiones superiores de python pygame aun no está del todo disponible.


```
python --version
```
Si es una versión del 3.13 o menos pasa a la instalación de requerimientos.


En caso de tener versiones incompatibles o que generen advertencias.


Verificar si tienes winget usando - sino instalarlo
```
winget --version
```
Luego para que no mezcles tus versiones de python en tu PC

```
winget install Python.Python.3.12 --override "/quiet InstallAllUsers=0 PrependPath=0"
```

Se recomienda usar un entorno virtual para que otros proyectos no sean afectados en caso de instalar más paquetes.
```
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
```
Entrar donde está el folder de pollo-cosmico e instalar desde ahí los requerimientos


```
pip install -r requirements.txt
python main.py
```

Vas a ver un rectángulo amarillo (el jugador de prueba) sobre un fondo oscuro,
con plataformas grises. Controles: flechas o WASD para moverte, ESPACIO/↑/W
para saltar. Esto sirve para probar física y colisiones — **no es el juego
final**, es un entorno de prueba.

## Qué hay en cada archivo

| Archivo | Qué hace |
|---|---|
| `main.py` | Punto de entrada |
| `src/core/game.py` | Loop principal |
| `src/core/state_manager.py` | Maneja qué escena está activa |
| `src/core/scene_base.py` | Clase base que deben heredar las escenas de Persona 2/3 |
| `src/core/settings.py` | Todas las constantes (velocidades, tiempos, colores, mapeo de teclas) |
| `src/core/asset_manager.py` | Carga y cachea imágenes/sonidos/fuentes (con placeholder magenta si el archivo no existe todavía) |
| `src/core/input_manager.py` | Traduce teclado a acciones con nombre (`"jump"`, `"left"`...) y soporta input scripteado para cinemáticas con auto-walk |
| `src/systems/physics.py` | `PhysicsBody`: gravedad, salto, coyote time, jump buffer |
| `src/systems/collision.py` | Resuelve colisiones AABB, incluye corner correction |
| `src/systems/camera.py` | Cámara con seguimiento suavizado y límites de nivel |
| `src/utils/pixelate.py` | Renderiza a baja resolución y escala sin suavizado (look pixel art) |
| `src/scenes/_physics_test_scene.py` | Escena de prueba **temporal** — bórrenla cuando MenuScene/PlayScene estén listas |
| `build/build_exe.bat` | Genera el `.exe` con PyInstaller (necesita que `build/icon.ico` exista) |

## Para Persona 2 (Player, enemigos, power-ups)

- Hereden de `PhysicsBody` (en `src/systems/physics.py`) para el `Player` y los enemigos que necesiten gravedad/salto.
- Usen `collision.move_and_collide(cuerpo, dt, lista_de_rects_solidos)` cada frame.
- Para leer el input: `game.input.is_pressed("right")`, `game.input.is_just_pressed("jump")`, etc. (acciones disponibles en `settings.ACTION_KEYS`).
- Para el modo auto-walk de las cinemáticas: `game.input.set_scripted_input({"right": True})` y `game.input.clear_scripted_input()` para devolver el control.

## Para Persona 3 (escenas, UI, audio)

- Hereden de `Scene` (`src/core/scene_base.py`) para `MenuScene`, `PlayScene`, `CinematicScene`, etc.
- Usen `game.assets.get_image(ruta, tamaño)` y `game.assets.get_sound(ruta)` — si el archivo de arte/sonido aún no existe, no truena: `get_image` devuelve un placeholder magenta de ese tamaño.
- Cuando `MenuScene` esté lista, avisen para cambiar `game.py` y que arranque ahí en vez de en `PhysicsTestScene`.

## Pendiente / no incluido aquí (no es de Persona 1)

- `entities/player.py`, `entities/enemy.py`, `entities/checkpoint.py` (Persona 2)
- `scenes/menu_scene.py`, `scenes/play_scene.py`, `scenes/cinematic_scene.py`, `scenes/pause_scene.py`, `scenes/gameover_scene.py`, `ui/`, `audio/audio_manager.py` (Persona 3)
- `systems/powerup_system.py` (Persona 2)
- `build/icon.ico` y todo lo de `assets/` (trabajo en conjunto)
