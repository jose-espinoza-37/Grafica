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
    ground = pygame.Rect(0, 160, 800, 20)
    platform_a = pygame.Rect(120, 120, 50, 8)   # esquina angosta: sirve para probar corner correction
    platform_b = pygame.Rect(420, 130, 70, 8)

    robot = Enemy(
        300, 140, width=16, height=20,
        patrol_min_x=280, patrol_max_x=360,
        is_mutant=False,  # Nivel 1: robots de seguridad, no mutantes
    )

    checkpoint = Checkpoint(400, 140)  # a mitad del recorrido (0 a 800)
    double_jump_item = PowerUpItem(150, 140, PowerUpItem.KIND_DOUBLE_JUMP)
    goal_rect = pygame.Rect(770, 110, 20, 50)

    return LevelConfig(
        start_pos=(20, 140),
        level_width=800,
        level_height=180,
        solids=[ground, platform_a, platform_b],
        enemies=[robot],
        checkpoint=checkpoint,
        powerup_items=[double_jump_item],
        goal_rect=goal_rect,
        has_danger=True,
        show_frasco_dialogue=True,  # único nivel con la línea de diálogo del frasco
        music_path=f"{settings.AUDIO_DIR}/music/nivel1.ogg",
    )


def _go_to_nivel1(game) -> None:
    player = Player(20, 140)
    config = _build_nivel1_config()
    scene = PlayScene(game, player, config, on_level_complete=lambda: _on_nivel1_complete(game))
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

    def _continue() -> None:
        # NOTA: Nivel 2, 3 y 4 se agregan con el mismo patrón que _go_to_nivel1.
        # Por ahora la demo termina aquí y vuelve al menú.
        game.states.switch_to(
            GameOverScene(
                game,
                message="Fin de la demo - continua en el Nivel 2",
                bg_color=settings.COLOR_BLACK,
                text_color=settings.COLOR_WHITE,
                hold_seconds=0.5,
            )
        )

    game.states.switch_to(CinematicScene(game, beats, on_finish=_continue))


# ======================================================================
# Rotación 4 (demo de la secuencia final) — La Isla
# ======================================================================

def start_rotacion4_demo(game) -> None:
    beat = build_botiquin_vacio_beat()
    game.states.switch_to(CinematicScene(game, [beat], on_finish=lambda: _go_to_isla_caminata(game)))


def _build_isla_config() -> LevelConfig:
    ground = pygame.Rect(0, 150, 600, 30)
    cave_entrance = pygame.Rect(560, 100, 30, 50)

    return LevelConfig(
        start_pos=(20, 130),
        level_width=600,
        level_height=180,
        solids=[ground],
        enemies=[],
        checkpoint=None,
        goal_rect=cave_entrance,
        has_danger=False,     # sin obstáculos, sin enemigos, sin power-ups
        show_hud=False,        # nada que mostrar: solo caminar, calma y melancolía
        music_path=f"{settings.AUDIO_DIR}/music/isla_calma.ogg",
    )


def _go_to_isla_caminata(game) -> None:
    player = Player(20, 130)
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
