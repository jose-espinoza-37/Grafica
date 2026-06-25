"""
settings.py
------------
Constantes globales del juego. Aquí viven todos los "números mágicos"
para que el resto del equipo (Persona 2 y Persona 3) no tenga que ir
a buscarlos dentro de la lógica de cada sistema.
"""

# --- Ventana ---
TITLE = "El Pollo Cósmico"
WINDOW_WIDTH = 1280
WINDOW_HEIGHT = 720
FPS = 60

# --- Render pixel art ---
# El juego se dibuja primero en una superficie pequeña (BASE_WIDTH x BASE_HEIGHT)
# y luego se escala hacia la ventana real. Esto es lo que da el look de pixel art.
BASE_WIDTH = 640
BASE_HEIGHT = 360
PIXEL_SCALE = WINDOW_WIDTH / BASE_WIDTH  # 2.0

# --- Colores (placeholders, el arte final los reemplaza) ---
COLOR_BG = (20, 18, 28)
COLOR_DEBUG_SOLID = (90, 200, 120)
COLOR_DEBUG_PLAYER = (240, 200, 60)
COLOR_WHITE = (255, 255, 255)
COLOR_BLACK = (0, 0, 0)

# --- Física / movimiento ---
GRAVITY = 2800.0            # px/s^2
MOVE_SPEED = 220.0          # px/s
JUMP_VELOCITY = -680.0      # px/s (negativo = hacia arriba)
MAX_FALL_SPEED = 1200.0     # px/s, velocidad terminal de caída

# Coyote time: margen para poder saltar justo después de salir de una plataforma.
COYOTE_TIME = 0.12          # segundos (tiempo puro, no escala con resolución)

# Jump buffer: si el jugador presiona saltar un poco ANTES de tocar el suelo,
# el salto se ejecuta igual en cuanto aterriza. Mejora la sensación de control.
JUMP_BUFFER_TIME = 0.10     # segundos

# Corner correction: cuántos píxeles como máximo se puede "empujar" al jugador
# hacia un costado para evitar que se pegue en la esquina de una plataforma
# al saltar casi perfecto.
CORNER_CORRECTION_MAX_PUSH = 12
CORNER_CORRECTION_ZONE = 20

# --- Cámara ---
CAMERA_SMOOTH = 0.12         # 0 = no se mueve, 1 = sigue instantáneo

# --- Input: mapeo de acciones a teclas ---
# Persona 2/3 deben usar estas acciones (input_manager.is_pressed("jump"), etc.)
# en vez de revisar teclas directamente, así si cambian el mapeo no rompen nada.
import pygame

ACTION_KEYS = {
    "left": (pygame.K_LEFT, pygame.K_a),
    "right": (pygame.K_RIGHT, pygame.K_d),
    "jump": (pygame.K_SPACE, pygame.K_UP, pygame.K_w),
    "attack": (pygame.K_j, pygame.K_z),
    "confirm": (pygame.K_RETURN, pygame.K_SPACE),
    "pause": (pygame.K_ESCAPE,),
}

# --- Rutas base ---
ASSETS_DIR = "assets"
SPRITES_DIR = f"{ASSETS_DIR}/sprites"
AUDIO_DIR = f"{ASSETS_DIR}/audio"
CINEMATICS_DIR = f"{ASSETS_DIR}/cinematics"
LEVELS_DIR = f"{ASSETS_DIR}/levels"
FONTS_DIR = f"{ASSETS_DIR}/fonts"

# --- Tilemaps (niveles diseñados en Tiled, ver systems/tilemap_loader.py) ---
TILE_SIZE = 16   # tamaño en píxeles de cada tile; usar el mismo en todos los niveles de Tiled

# ======================================================================
# A partir de aquí: constantes agregadas por Persona 2 (Player, enemigos,
# power-ups, checkpoint y mecánicas de nivel). Mismo archivo compartido,
# no uno nuevo, para que todo siga en un solo lugar.
# ======================================================================

# --- Player: tamaño y vida/transformación ---
PLAYER_WIDTH = 28
PLAYER_HEIGHT = 40
HIT_INVULNERABILITY_TIME = 0.8     # segundos de invulnerabilidad tras recibir un golpe

# --- Player: ataque (mecánica de tutorial del Nivel 1) ---
PLAYER_ATTACK_RANGE = 28            # ancho del hitbox de ataque, en píxeles
PLAYER_ATTACK_DURATION = 0.15        # segundos que el hitbox de ataque está activo
PLAYER_ATTACK_COOLDOWN = 0.35        # segundos antes de poder atacar de nuevo

# --- Power-ups ---
DISGUISE_DURATION = 15.0             # segundos de inmunidad de "Yo También Digo Pío"

# --- Enemigos ---
ENEMY_ATTACK_COOLDOWN = 1.0          # segundos entre golpes del mismo enemigo
ENEMY_PATROL_SPEED = 80.0            # px/s, velocidad de patrulla por defecto

# --- Mecánicas de nivel ---
BOOST_PAD_VELOCITY = -920.0          # impulso vertical de las raíces/plataformas (Nivel 3, bosque)

# --- Colores de depuración para las entidades de Persona 2 ---
COLOR_CHECKPOINT_OFF = (120, 100, 60)
COLOR_CHECKPOINT_ON = (240, 210, 90)
COLOR_ENEMY_ROBOT = (150, 150, 160)
COLOR_ENEMY_MUTANT = (200, 90, 70)
COLOR_GRAVITY_ZONE = (120, 90, 220)
COLOR_BOOST_PAD = (90, 200, 160)
COLOR_CYCLIC_PLATFORM = (210, 170, 90)
COLOR_POWERUP_DOUBLE_JUMP = (250, 230, 140)
COLOR_POWERUP_DISGUISE = (250, 170, 60)
COLOR_PLAYER_HUMAN = (240, 200, 60)
COLOR_PLAYER_TRANSFORMED = (235, 235, 235)
