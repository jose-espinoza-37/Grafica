"""
intro_flow.py
---------------
Aquí se conecta todo lo demás: cinemáticas + niveles, en el orden de la
historia. Es el único archivo que "sabe" la trama completa - el resto de
las escenas son piezas genéricas reutilizables.

Incluye dos puntos de entrada (ambos accesibles desde MenuScene):

  - start_new_game(game): cinemática inicial -> Nivel 1 jugable (con
    robot, checkpoint, ítem de power-up y meta) -> frasco -> transición.
    Sirve como ejemplo completo y probado de cómo armar un LevelConfig.
    Los Niveles 2, 3 y 4 (jugables) se agregan con el mismo patrón.

  - start_rotacion4_demo(game): la secuencia completa de la Rotación 4
    (botiquín vacío -> caminata calma -> cueva -> El Legado -> última
    rotación con las líneas agregadas -> luz blanca -> silencio ->
    postcréditos). Botón directo en el menú para poder revisarla sin
    tener que jugar primero los otros 3 niveles.
"""

from __future__ import annotations
import pygame

from src.core import settings
from src.entities.player import Player
from src.entities.enemy import Enemy
from src.entities.checkpoint import Checkpoint
from src.entities.powerup_item import PowerUpItem
from src.entities.gravity_zone import GravityZone
from src.entities.boost_pad import BoostPad
from src.entities.cyclic_platform import CyclicPlatform
from src.scenes.play_scene import PlayScene, LevelConfig
from src.scenes.cinematic_scene import CinematicScene, CinematicBeat, build_botiquin_vacio_beat
from src.scenes.gameover_scene import GameOverScene


# ======================================================================
# Nivel 1 (demo jugable) — Instalación Militar
# ======================================================================

def start_new_game(game) -> None:
    beats = [
        CinematicBeat(
            image_path=f"{settings.CINEMATICS_DIR}/lab_alarma.png",
            lines=[
                "Instalación militar subterránea. Los científicos monitorean al Pollo Cósmico.",
                "Las pantallas muestran lecturas anormales. Suenan alarmas. Las luces parpadean.",
            ],
        ),
        CinematicBeat(
            image_path=f"{settings.CINEMATICS_DIR}/rotacion_1_detectada.png",
            lines=["ROTACIÓN 1 DETECTADA"],
        ),
        CinematicBeat(
            image_path=f"{settings.CINEMATICS_DIR}/elias_escapa.png",
            lines=[
                "Comienza la evacuación. Elías roba la información clasificada...",
                "...y un pequeño botiquín con 3 frascos contra los efectos de La Brasa.",
            ],
        ),
    ]
    game.states.switch_to(CinematicScene(game, beats, on_finish=lambda: _go_to_nivel1(game)))


def _build_nivel1_config() -> LevelConfig:
    ground = pygame.Rect(0, 320, 1600, 40)
    platform_a = pygame.Rect(240, 240, 100, 16)  # esquina angosta: sirve para probar corner correction
    platform_b = pygame.Rect(840, 260, 140, 16)

    robot = Enemy(
        600, 280, width=32, height=40,
        patrol_min_x=560, patrol_max_x=720,
        is_mutant=False,  # Nivel 1: robots de seguridad, no mutantes
    )

    checkpoint = Checkpoint(800, 280, 48, 40)  # a mitad del recorrido (0 a 1600)
    double_jump_item = PowerUpItem(300, 280, PowerUpItem.KIND_DOUBLE_JUMP, width=24, height=24)
    goal_rect = pygame.Rect(1540, 220, 40, 100)

    return LevelConfig(
        start_pos=(40, 280),
        level_width=1600,
        level_height=360,
        solids=[ground, platform_a, platform_b],
        enemies=[robot],
        checkpoint=checkpoint,
        powerup_items=[double_jump_item],
        goal_rect=goal_rect,
        has_danger=True,
        show_frasco_dialogue=True,  # único nivel con la línea de diálogo del frasco
        music_path=f"{settings.AUDIO_DIR}/music/nivel1.ogg",
        background_path=f"{settings.ASSETS_DIR}/backgrounds/nivel1.png",
        background_parallax=0.5,
    )


def _go_to_nivel1(game) -> None:
    player = Player(40, 280)
    config = _build_nivel1_config()
    scene = PlayScene(game, player, config,
                      on_level_complete=lambda: _on_nivel1_complete(game),
                      on_restart=lambda: _go_to_nivel1(game))
    game.states.switch_to(scene)


def _on_nivel1_complete(game) -> None:
    beats = [
        CinematicBeat(
            image_path=f"{settings.CINEMATICS_DIR}/superficie_pollo.png",
            lines=[
                "Al salir a la superficie, Elías observa por primera vez al Pollo Cósmico.",
                "La criatura cambia lentamente de color. El mundo entero tiembla.",
            ],
        ),
    ]

    game.states.switch_to(CinematicScene(game, beats, on_finish=lambda: _go_to_nivel2(game)))


# ======================================================================
# Nivel 2 (jugable) — Ciudad Evacuada (zonas de gravedad alterada)
# ======================================================================

def _build_nivel2_config() -> LevelConfig:
    ground = pygame.Rect(0, 320, 2000, 40)

    plat_alta_a = pygame.Rect(560, 180, 120, 16)   # solo se alcanza con gravedad ligera
    plat_media  = pygame.Rect(900, 240, 140, 16)

    zona_ligera = GravityZone(500, 110, 260, 210, gravity_scale=0.3)   # flotás hacia arriba
    zona_pesada = GravityZone(1300, 200, 200, 120, gravity_scale=1.8)  # sector "plomo"

    mutante_1 = Enemy(700, 280, width=32, height=40,
                      patrol_min_x=640, patrol_max_x=820, is_mutant=True)
    mutante_2 = Enemy(1500, 280, width=32, height=40,
                      patrol_min_x=1440, patrol_max_x=1620, is_mutant=True)

    checkpoint = Checkpoint(1000, 280, 48, 40)  # a mitad de 0..2000

    disfraz     = PowerUpItem(450, 280, PowerUpItem.KIND_DISGUISE, width=24, height=24)
    doble_salto = PowerUpItem(1150, 280, PowerUpItem.KIND_DOUBLE_JUMP, width=24, height=24)

    goal_rect = pygame.Rect(1940, 220, 40, 100)

    return LevelConfig(
        start_pos=(40, 280),
        level_width=2000,
        level_height=360,
        solids=[ground, plat_alta_a, plat_media],
        enemies=[mutante_1, mutante_2],
        checkpoint=checkpoint,
        gravity_zones=[zona_ligera, zona_pesada],
        powerup_items=[disfraz, doble_salto],
        goal_rect=goal_rect,
        has_danger=True,
        music_path=f"{settings.AUDIO_DIR}/music/nivel2.ogg",
        background_path=f"{settings.ASSETS_DIR}/backgrounds/nivel2.png",
        background_parallax=0.4,
    )


def _start_nivel2_gameplay(game) -> None:
    player = Player(40, 280)
    config = _build_nivel2_config()
    scene = PlayScene(game, player, config,
                      on_level_complete=lambda: _go_to_nivel3(game),
                      on_restart=lambda: _start_nivel2_gameplay(game))
    game.states.switch_to(scene)


def _go_to_nivel2(game) -> None:
    beats = [
        CinematicBeat(
            image_path=f"{settings.CINEMATICS_DIR}/rotacion_2_detectada.png",
            lines=["ROTACIÓN 2/4"],
        ),
    ]
    game.states.switch_to(CinematicScene(game, beats, on_finish=lambda: _start_nivel2_gameplay(game)))


# ======================================================================
# Nivel 3 (jugable) — Bosque Mutante -> Playa Distorsionada
# ======================================================================

def _build_nivel3_config() -> LevelConfig:
    ground = pygame.Rect(0, 320, 2200, 40)

    pad_1 = BoostPad(300, 300, 60, 20)
    pad_2 = BoostPad(740, 300, 60, 20)
    plat_bosque_a = pygame.Rect(270, 160, 120, 16)
    plat_bosque_b = pygame.Rect(700, 200, 130, 16)

    mutante_bosque = Enemy(520, 280, width=32, height=40,
                           patrol_min_x=460, patrol_max_x=640, is_mutant=True)

    checkpoint = Checkpoint(1100, 280, 48, 40)  # transición bosque -> playa

    ciclo_1 = CyclicPlatform(1320, 260, 100, 16, visible_time=2.0, hidden_time=1.5, start_visible=True)
    ciclo_2 = CyclicPlatform(1560, 230, 100, 16, visible_time=1.5, hidden_time=1.5, start_visible=False)
    ciclo_3 = CyclicPlatform(1820, 260, 100, 16, visible_time=2.0, hidden_time=1.2, start_visible=True)

    mutante_playa = Enemy(1700, 280, width=32, height=40,
                          patrol_min_x=1640, patrol_max_x=1900, is_mutant=True)

    disfraz = PowerUpItem(150, 280, PowerUpItem.KIND_DISGUISE, width=24, height=24)

    goal_rect = pygame.Rect(2140, 220, 40, 100)

    return LevelConfig(
        start_pos=(40, 280),
        level_width=2200,
        level_height=360,
        solids=[ground, plat_bosque_a, plat_bosque_b],
        enemies=[mutante_bosque, mutante_playa],
        checkpoint=checkpoint,
        boost_pads=[pad_1, pad_2],
        cyclic_platforms=[ciclo_1, ciclo_2, ciclo_3],
        powerup_items=[disfraz],
        goal_rect=goal_rect,
        has_danger=True,
        music_path=f"{settings.AUDIO_DIR}/music/nivel3.ogg",
        background_path=f"{settings.ASSETS_DIR}/backgrounds/nivel3a.png",       # bosque
        background_path_2=f"{settings.ASSETS_DIR}/backgrounds/nivel3b.png",     # playa
        background_switch_x=1100,  # cambia en el checkpoint (bosque -> playa)
        background_parallax=0.5,
    )


def _start_nivel3_gameplay(game) -> None:
    player = Player(40, 280)
    config = _build_nivel3_config()
    scene = PlayScene(game, player, config,
                      on_level_complete=lambda: start_rotacion4_demo(game),
                      on_restart=lambda: _start_nivel3_gameplay(game))
    game.states.switch_to(scene)


def _go_to_nivel3(game) -> None:
    beats = [
        CinematicBeat(
            image_path=f"{settings.CINEMATICS_DIR}/rotacion_3_detectada.png",
            lines=["ROTACIÓN 3/4"],
        ),
    ]
    game.states.switch_to(CinematicScene(game, beats, on_finish=lambda: _start_nivel3_gameplay(game)))


# ======================================================================
# Rotación 4 (demo de la secuencia final) — La Isla
# ======================================================================

def start_rotacion4_demo(game) -> None:
    beats = [
        CinematicBeat(
            image_path=f"{settings.CINEMATICS_DIR}/rotacion_4_detectada.png",
            lines=["ROTACIÓN 4/4"],
        ),
        build_botiquin_vacio_beat(),
    ]
    game.states.switch_to(CinematicScene(game, beats, on_finish=lambda: _go_to_isla_caminata(game)))


def _build_isla_config() -> LevelConfig:
    ground = pygame.Rect(0, 300, 1200, 60)
    cave_entrance = pygame.Rect(1120, 200, 60, 100)

    return LevelConfig(
        start_pos=(40, 260),
        level_width=1200,
        level_height=360,
        solids=[ground],
        enemies=[],
        checkpoint=None,
        goal_rect=cave_entrance,
        has_danger=False,     # sin obstáculos, sin enemigos, sin power-ups
        show_hud=False,        # nada que mostrar: solo caminar, calma y melancolía
        music_path=f"{settings.AUDIO_DIR}/music/isla_calma.ogg",
        background_path=f"{settings.ASSETS_DIR}/backgrounds/nivel4.png",
        background_parallax=0.5,
    )


def _go_to_isla_caminata(game) -> None:
    player = Player(40, 260)
    config = _build_isla_config()
    scene = PlayScene(game, player, config, on_level_complete=lambda: _go_to_cueva(game))
    game.states.switch_to(scene)


def _go_to_cueva(game) -> None:
    beats = [
        CinematicBeat(
            image_path=f"{settings.CINEMATICS_DIR}/cueva_murales.png",
            lines=[
                "La cueva contiene restos de antiguas civilizaciones: murales, observatorios",
                "y representaciones del Pollo Cósmico.",
            ],
        ),
        CinematicBeat(
            image_path=f"{settings.CINEMATICS_DIR}/cueva_revelacion.png",
            lines=[
                "Elías comprende finalmente la verdad: los mayas no desaparecieron por una",
                "guerra ni por una catástrofe común. Fueron testigos del último ciclo.",
                "Y ahora la humanidad está destinada a convertirse en la siguiente civilización perdida.",
            ],
        ),
        CinematicBeat(
            image_path=f"{settings.CINEMATICS_DIR}/legado.png",
            lines=[
                "Elías construye un pequeño refugio con materiales de la isla y escribe todo",
                "lo que aprendió: qué es el Pollo Cósmico, qué pasó con los mayas y qué le",
                "ocurrirá a la humanidad. También deja diagramas, mapas y gráficas astronómicas.",
            ],
        ),
        CinematicBeat(
            image_path=f"{settings.CINEMATICS_DIR}/acantilado.png",
            lines=[
                "Desde un acantilado, Elías observa el cielo.",
                "El Pollo inicia lentamente su última rotación. La realidad comienza a deformarse.",
            ],
        ),
        CinematicBeat(
            image_path=f"{settings.CINEMATICS_DIR}/acantilado.png",
            lines=[
                "Quizá no era el fin del mundo...",
                "Quizá solo era el momento de darle la vuelta.",
            ],
        ),
        CinematicBeat(
            image_path=f"{settings.CINEMATICS_DIR}/elias_sonrie.png",
            lines=["La vida da vueltas como un pollo a la brasa."],
        ),
    ]
    game.states.switch_to(CinematicScene(game, beats, on_finish=lambda: _go_to_luz_blanca(game)))


def _go_to_luz_blanca(game) -> None:
    # Luz blanca -> silencio (oscuridad) -> postcréditos, encadenado sin necesitar
    # que el jugador presione nada (auto_continue=True), tal como lo describe
    # el documento de diseño.
    pantalla_negra = GameOverScene(
        game, bg_color=settings.COLOR_BLACK, hold_seconds=1.5,
        auto_continue=True, on_finish=lambda: _go_to_postcreditos(game),
    )
    pantalla_blanca = GameOverScene(
        game, bg_color=settings.COLOR_WHITE, hold_seconds=1.5,
        auto_continue=True, on_finish=lambda: game.states.switch_to(pantalla_negra),
    )
    game.states.switch_to(pantalla_blanca)


def _go_to_postcreditos(game) -> None:
    beats = [
        CinematicBeat(
            image_path=f"{settings.CINEMATICS_DIR}/postcreditos_futuro.png",
            lines=[
                "Miles de años después. Una nueva civilización, con tecnología avanzada,",
                "domina el planeta.",
            ],
        ),
        CinematicBeat(
            image_path=f"{settings.CINEMATICS_DIR}/postcreditos_ruinas.png",
            lines=["Un grupo de arqueólogos descubre las ruinas de la isla y los escritos de Elías."],
        ),
        CinematicBeat(
            image_path=f"{settings.CINEMATICS_DIR}/postcreditos_estudio.png",
            lines=[
                '"Parece que esta civilización adoraba múltiples deidades primitivas."',
                '"Sí. Aquí menciona algo llamado Dios WiFi. Y aquí, Dios Celular."',
            ],
        ),
        CinematicBeat(
            image_path=f"{settings.CINEMATICS_DIR}/postcreditos_descartan.png",
            lines=[
                '"Probablemente otra superstición.',
                'Las civilizaciones antiguas siempre inventaban historias para explicar lo que no comprendían."',
            ],
        ),
        CinematicBeat(
            image_path=f"{settings.CINEMATICS_DIR}/postcreditos_sombra.png",
            lines=[""],  # la cámara se eleva hacia el cielo; aparece la sombra del Pollo, sin texto
        ),
    ]
    game.states.switch_to(
        CinematicScene(game, beats, on_finish=lambda: game.states.switch_to(
            GameOverScene(game, message="", bg_color=settings.COLOR_BLACK, hold_seconds=2.0)
        ))
    )
