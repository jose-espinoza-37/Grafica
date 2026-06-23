"""
settings.py
------------
Constantes globales del juego. Aquí viven todos los "números mágicos"
para que el resto del equipo (Persona 2 y Persona 3) no tenga que ir
a buscarlos dentro de la lógica de cada sistema.
"""

# --- Ventana ---
TITLE = "El Pollo Cósmico"
WINDOW_WIDTH = 1024
WINDOW_HEIGHT = 576
FPS = 60

# --- Render pixel art ---
# El juego se dibuja primero en una superficie pequeña (BASE_WIDTH x BASE_HEIGHT)
# y luego se escala hacia la ventana real. Esto es lo que da el look de pixel art.
BASE_WIDTH = 320
BASE_HEIGHT = 180
PIXEL_SCALE = WINDOW_WIDTH / BASE_WIDTH  # factor de escalado para la ventana

# --- Colores (placeholders, el arte final los reemplaza) ---
COLOR_BG = (20, 18, 28)
COLOR_DEBUG_SOLID = (90, 200, 120)
COLOR_DEBUG_PLAYER = (240, 200, 60)
COLOR_WHITE = (255, 255, 255)
COLOR_BLACK = (0, 0, 0)

# --- Física / movimiento ---
GRAVITY = 1400.0            # px/s^2
MOVE_SPEED = 110.0          # px/s
JUMP_VELOCITY = -340.0      # px/s (negativo = hacia arriba)
MAX_FALL_SPEED = 600.0      # px/s, velocidad terminal de caída

# Coyote time: margen para poder saltar justo después de salir de una plataforma.
COYOTE_TIME = 0.12          # segundos

# Jump buffer: si el jugador presiona saltar un poco ANTES de tocar el suelo,
# el salto se ejecuta igual en cuanto aterriza. Mejora la sensación de control.
JUMP_BUFFER_TIME = 0.10     # segundos

# Corner correction: cuántos píxeles como máximo se puede "empujar" al jugador
# hacia un costado para evitar que se pegue en la esquina de una plataforma
# al saltar casi perfecto.
CORNER_CORRECTION_MAX_PUSH = 6   # píxeles
CORNER_CORRECTION_ZONE = 10      # qué tan cerca del borde superior se activa la revisión

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
