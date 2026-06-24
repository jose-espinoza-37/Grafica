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





# Persona 2 — Player, Enemigos, Power-ups y Checkpoint

Todo este código ya está probado (ver pruebas automáticas más abajo) y se integra
directamente con lo de Persona 1 (`PhysicsBody`, `collision.move_and_collide`,
`Camera`, `InputManager`).

## Qué hay en cada archivo

| Archivo | Qué hace |
|---|---|
| `src/entities/entity_base.py` | Clase base mínima (`update`, `draw`, `draw_placeholder`) |
| `src/entities/player.py` | El jugador: movimiento, salto (incluye el extra de Pluma Cósmica), ataque, vida/transformación, respawn |
| `src/systems/powerup_system.py` | `PowerUpManager`: Pluma Cósmica (doble salto) + Yo También Digo Pío (disfraz) |
| `src/entities/powerup_item.py` | Ítem recogible en el nivel que entrega un power-up |
| `src/entities/enemy.py` | Robots (Nivel 1) y mutantes con pico (Nivel 2/3), patrulla + ataque por contacto + ciclo opcional de aparecer/desaparecer |
| `src/entities/checkpoint.py` | Punto de respawn a mitad de nivel (lógica únicamente, el sprite final no es una bandera) |
| `src/entities/cyclic_timer.py` | Temporizador reutilizable para cosas que aparecen/desaparecen en ciclos fijos |
| `src/entities/cyclic_platform.py` | Plataforma cíclica (mitad de playa, Nivel 3) |
| `src/entities/gravity_zone.py` | Zonas de gravedad alterada (Nivel 2) |
| `src/entities/boost_pad.py` | Raíces/plataformas que impulsan el salto (mitad de bosque, Nivel 3) |

## Cómo se conecta todo (lo que Persona 3 debe hacer en PlayScene)

```python
gscale = get_gravity_scale(player.rect, gravity_zones)
player.update(dt, game.input, level_solids, gravity_scale=gscale)

for enemy in enemies:
    enemy.update(dt)
    if enemy.active and enemy.rect.colliderect(player.rect):
        enemy.try_attack(player)

atk = player.attack_rect
if atk:
    for enemy in enemies:
        if enemy.alive and atk.colliderect(enemy.rect):
            enemy.take_damage()

for pad in boost_pads:
    pad.try_boost(player)

for item in powerup_items:
    item.try_collect(player)

if checkpoint.check(player.rect):
    reproducir_sonido_de_checkpoint()  # opcional, feedback de Persona 3

if player.defeated:
    player.respawn_at(checkpoint.respawn_point)

# al terminar el nivel (cutscene del frasco):
player.heal_full()
```

`level_solids` debe incluir los sólidos fijos del nivel **más** los
`platform.solid_rect` de cada `CyclicPlatform` que esté visible en ese
frame (los que estén invisibles devuelven `None`, hay que filtrarlos).

## Reglas importantes para no romper la coherencia del diseño

- El power-up de disfraz (`PowerUpItem.KIND_DISGUISE`) **no debe colocarse en el Nivel 1** — los robots no son mutantes (`Enemy(..., is_mutant=False)`), así que no tendría sentido ahí.
- Los enemigos de Nivel 2 y Nivel 3 deben crearse con `is_mutant=True` (es el valor por defecto).
- El golpe del jugador siempre quita los power-ups activos (`PowerUpManager.clear_all()`), eso ya está dentro de `Player.take_hit()`, no hay que llamarlo aparte.
- Las cinemáticas con auto-walk (Persona 3) **no necesitan tocar este código**: si activan el modo scripteado en el `InputManager`, `Player.update()` ya lo lee de forma transparente a través de `is_pressed`/`is_just_pressed`.

## Pruebas que ya se corrieron (todas pasaron)

1. 3 golpes seguidos transforman al jugador en pollo completo y lo marcan `defeated`.
2. El disfraz bloquea el daño de un enemigo mutante, pero no el de un robot.
3. Recibir un golpe quita el doble salto y el disfraz si estaban activos.
4. El checkpoint se activa una sola vez y `respawn_at` devuelve al jugador a forma humana.
5. `heal_full()` (el frasco de fin de nivel) revierte cualquier transformación.
6. Recoger un `PowerUpItem` habilita el power-up correspondiente.
7. El enemigo patrulla, ataca con cooldown, y muere de un golpe del jugador.
8. Un enemigo con ciclo alterna correctamente entre activo/invisible.
9. `GravityZone` devuelve el `gravity_scale` correcto dentro y fuera de la zona.
10. `BoostPad` impulsa al jugador hacia arriba solo si está cayendo/quieto.
11. `CyclicPlatform` alterna su `solid_rect` entre un rect real y `None`.
12. Integración completa: 180 frames de gameplay real (Player + Enemy + Checkpoint + GravityZone + PowerUpItem + cámara + dibujo) sin ningún error.

## Pendiente / no incluido aquí (no es de Persona 2)

- `scenes/menu_scene.py`, `scenes/play_scene.py` (donde se conecta todo esto), `scenes/cinematic_scene.py`, `ui/hud.py`, `audio/audio_manager.py` (Persona 3)
- Sprites reales para cada etapa de transformación, enemigos, ítems, checkpoint (trabajo en conjunto)
- Diseño concreto de cada nivel: dónde van exactamente los enemigos, zonas de gravedad, boost pads y power-ups (trabajo en conjunto, en `assets/levels/`)









# Persona 3 — Escenas, Cinemáticas, UI y Audio

Todo este paquete ya está probado de punta a punta (ver pruebas más abajo) y
se integra con lo de Persona 1 y Persona 2 sin tocar su lógica interna.


## Qué hay en este paquete

```
src/
├── ui/
│   ├── dialogue_box.py     # Caja de texto reutilizable (diálogos y cinemáticas)
│   ├── button.py           # Button + ButtonMenu (navegación con izquierda/derecha + confirm)
│   └── hud.py               # Indicador de vida/transformación y power-ups activos
├── audio/
│   └── audio_manager.py    # Música y efectos de sonido (sobre AssetManager / pygame.mixer)
└── scenes/
    ├── cinematic_scene.py   # Motor de cutscenes tipo collage (fotos fijas + texto)
    ├── menu_scene.py         # Menú principal
    ├── pause_scene.py        # Pausa (se apila encima de PlayScene)
    ├── gameover_scene.py     # Pantallas de cierre (luz blanca, "fin de demo", etc.)
    ├── play_scene.py         # Escena de gameplay genérica (conecta Player/Enemy/Checkpoint/etc.)
    └── intro_flow.py         # Wiring de la historia completa (cinemáticas + niveles en orden)

CAMBIOS_PERSONA1/
└── src/core/game.py         # Archivo de Persona 1 MODIFICADO (ver sección abajo)
```

## Cómo se conecta todo

- **`cinematic_scene.py`**: una cutscene es una lista de `CinematicBeat` (cada uno con una imagen fija y/o texto). Avanza con "confirm". Si una cinemática necesita "moverse" (como Elías caminando hacia la cueva), eso **no pasa aquí** — se hace con `intro_autowalk_seconds` en `PlayScene`, reusando el gameplay real de Persona 2.
- **`play_scene.py`**: recibe un `LevelConfig` (sólidos, enemigos, checkpoint, zonas de gravedad, etc. — todo de Persona 2) y un `Player` (Persona 2), y cada frame: actualiza física/colisión, resuelve combate jugador↔enemigo, checkpoint, respawn, y dispara la cutscene del frasco al llegar a la meta (`goal_rect`).
- **`intro_flow.py`**: es el único archivo que conoce la trama completa. Tiene dos puntos de entrada, ambos con botón en el menú:
  - `start_new_game`: cinemática inicial -> **Nivel 1 jugable** (robot, checkpoint, ítem de doble salto, meta) -> frasco -> transición -> pantalla de "fin de demo".
  - `start_rotacion4_demo`: botiquín vacío -> caminata calma en la isla -> cueva/legado/última rotación (con las dos líneas que pidieron agregar) -> luz blanca -> silencio -> postcréditos. Pensado para poder revisar esa secuencia sin tener que jugar antes los otros niveles.

## Cambios en archivos de Persona 1 (para diferenciar bien)

Solo modifiqué **un archivo que no es mío**: `src/core/game.py`. Los cambios fueron:

1. Se agregó `self.audio = AudioManager(self.assets)` en `Game.__init__`, con su import correspondiente.
2. En `Game.run()`, la escena inicial cambió de la escena de prueba de Persona 1 (`PhysicsTestScene`) a `MenuScene` (la real, de Persona 3) — tal como decía la nota que dejó Persona 1 en su propio código ("reemplazar por MenuScene apenas esté lista").

Nada más cambió en ese archivo. Lo incluyo completo dentro de `CAMBIOS_PERSONA1/src/core/game.py` para que puedan reemplazarlo directamente, y aquí queda documentado por si prefieren aplicar el cambio a mano en su copia.

No toqué ningún archivo de Persona 2.

## Decisiones que tomé (avísenme si quieren algo distinto)

- **Navegación de menús**: como `settings.ACTION_KEYS` no tiene "arriba/abajo", los botones se navegan con izquierda/derecha + confirm (sin soporte de mouse por ahora — mapear la posición del mouse de la ventana real a la superficie de baja resolución necesita un cálculo que vive en `pixelate.py` y no estaba expuesto).
- **Combate del Nivel 1**: el robot muere de un solo golpe del ataque del jugador (sin barra de vida en los enemigos) — lo más simple para una jam, ya lo había asumido también al hacer el código de Persona 2.
- **GameOverScene "FIN"**: no existe una derrota real en el diseño (morir solo manda al checkpoint), así que reutilicé esta escena para los cierres de pantalla completa (luz blanca, silencio, postcréditos), no para una derrota.
- **La cinemática de la cueva incluye, en un solo `CinematicScene`, tanto los murales/revelación como El Legado y la Última Rotación con las dos líneas agregadas** ("Quizá no era el fin del mundo... / Quizá solo era el momento de darle la vuelta."), seguido de la frase final. Si prefieren separarlo en más pantallas o cambiar el ritmo, es solo editar la lista de `beats` en `intro_flow.py`, no hay que tocar `cinematic_scene.py`.

## Pruebas que ya se corrieron (todas pasaron)

Simulé pulsaciones de teclado reales (no solo imports) para recorrer el juego de punta a punta:

1. **Flujo completo del Nivel 1**: Menú -> confirmar "Jugar" -> cinemática inicial (3 beats) -> Nivel 1 jugable -> caminar hasta la meta -> cutscene del frasco (con diálogo) -> cinemática de transición -> pantalla "Fin de la demo". Sin errores.
2. **Pausa**: presionar "pause" dentro de PlayScene apila PauseScene (stack size 2) y la congela; presionar "pause" de nuevo la reanuda exactamente donde quedó.
3. **Combate y transformación dentro del gameplay real**: caminar hacia el robot del Nivel 1 produce un golpe real (`player.stage` sube), y seguir caminando hasta la meta dispara `heal_full()` correctamente.
4. **Flujo completo de la demo de Rotación 4**: Menú -> "Ver Rotación 4" -> botiquín vacío -> caminata por la isla (sin HUD, sin peligro) -> cinemática de la cueva/legado/última rotación (con las líneas agregadas) -> cadena automática luz blanca -> negro -> postcréditos (sin necesitar ningún input) -> postcréditos (5 beats) -> pantalla final negra. Sin errores.

## Pendiente / sugerencias para seguir

- Agregar los Niveles 2, 3 y 4 jugables con el mismo patrón que `_build_nivel1_config()` en `intro_flow.py` (ahí ya se usan zonas de gravedad, boost pads y plataformas cíclicas de Persona 2, solo falta posicionarlas según el diseño real de cada nivel).
- Cuando haya sprites/fondos reales, las rutas ya están listas en `settings.CINEMATICS_DIR`, `settings.SPRITES_DIR`, `settings.AUDIO_DIR` — solo hay que poner los archivos ahí con los nombres que ya usa `intro_flow.py` (ej. `lab_alarma.png`, `frasco.png`, `acantilado.png`...).
- Si agregan mouse a los menús, `ButtonMenu.handle_click(pos)` ya está listo, solo falta la conversión de coordenadas ventana -> render en `pixelate.py`.



