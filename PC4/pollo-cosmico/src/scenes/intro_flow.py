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

from src.core import settings
from src.entities.player import Player
from src.systems.tilemap_loader import load_level
from src.scenes.play_scene import PlayScene
from src.scenes.cinematic_scene import CinematicScene, CinematicBeat, build_botiquin_vacio_beat
from src.scenes.gameover_scene import GameOverScene


# ======================================================================
# Carga de niveles desde JSON (Tiled) — reemplaza el armado a mano.
# Cada nivel vive en assets/levels/nivel_N.json. La música y los flags de
# historia (has_danger, dialogo del frasco, etc.) que el .json no define se
# aplican aquí sobre el LevelConfig ya cargado.
# ======================================================================

_LEVEL_PATHS = {
    1: f"{settings.LEVELS_DIR}/nivel_1.json",
    2: f"{settings.LEVELS_DIR}/nivel_2.json",
    3: f"{settings.LEVELS_DIR}/nivel_3.json",
    4: f"{settings.LEVELS_DIR}/nivel_4.json",
}

_LEVEL_META = {
    1: dict(music_path=f"{settings.AUDIO_DIR}/music/nivel1.mp3",
            has_danger=True, show_frasco_dialogue=True, intro_autowalk_seconds=1.2,
            background_path=f"{settings.BACKGROUNDS_DIR}/nivel1.png"),
    2: dict(music_path=f"{settings.AUDIO_DIR}/music/nivel2.mp3",
            has_danger=True, show_frasco_dialogue=False,
            background_path=f"{settings.BACKGROUNDS_DIR}/nivel2.png"),
    3: dict(has_danger=True, show_frasco_dialogue=False,
            music_path=f"{settings.AUDIO_DIR}/music/nivel3a.mp3",
            background_path=f"{settings.BACKGROUNDS_DIR}/nivel3_combinado.png",
            background_parallax=0.4),
    4: dict(music_path=f"{settings.AUDIO_DIR}/music/isla_calma.mp3",
            has_danger=False, show_hud=False,
            background_path=f"{settings.BACKGROUNDS_DIR}/nivel4.png"),
}


def _make_level_factory(level_number: int, game):
    """Devuelve una función sin argumentos que carga el nivel desde su .json.
    PlayScene la usa para 'Reiniciar nivel' y para reaparecer con estado limpio."""
    path = _LEVEL_PATHS[level_number]
    meta = _LEVEL_META.get(level_number, {})

    def factory():
        config, renderer = load_level(path, game.assets)
        config.tilemap_renderer = renderer
        for key, value in meta.items():
            setattr(config, key, value)
        return config

    return factory


def _start_level(game, level_number: int, on_complete) -> None:
    """Carga el nivel desde su .json y entra a PlayScene."""
    factory = _make_level_factory(level_number, game)
    config = factory()
    player = Player(*config.start_pos)
    scene = PlayScene(game, player, config,
                      on_level_complete=on_complete, level_factory=factory)
    game.states.switch_to(scene)


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
    game.audio.play_music(settings.MUSIC_LEVEL_1)
    game.states.switch_to(CinematicScene(game, beats, on_finish=lambda: _go_to_nivel1(game)))


def _go_to_nivel1(game) -> None:
    _start_level(game, 1, on_complete=lambda: _on_nivel1_complete(game))


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

    game.audio.play_music(settings.MUSIC_LEVEL_2)
    game.states.switch_to(CinematicScene(game, beats, on_finish=lambda: _go_to_nivel2(game)))


# ======================================================================
# Nivel 2 — Ciudad Evacuada
# ======================================================================

def _go_to_nivel2(game) -> None:
    _start_level(game, 2, on_complete=lambda: _on_nivel2_complete(game))


def _on_nivel2_complete(game) -> None:
    beats = [
        CinematicBeat(
            image_path=f"{settings.CINEMATICS_DIR}/ciudad_rotacion.png",
            lines=[
                "Nueva rotación. Edificios enteros comienzan a elevarse.",
                "El Pollo brilla con un tono rojizo.",
            ],
        ),
    ]
    game.audio.play_music(f"{settings.AUDIO_DIR}/music/nivel3a.mp3")
    game.states.switch_to(CinematicScene(game, beats, on_finish=lambda: _go_to_nivel3(game)))


# ======================================================================
# Nivel 3 — Bosque -> Playa
# ======================================================================

def _go_to_nivel3(game) -> None:
    _start_level(game, 3, on_complete=lambda: _on_nivel3_complete(game))


def _on_nivel3_complete(game) -> None:
    beats = [
        CinematicBeat(
            image_path=f"{settings.CINEMATICS_DIR}/oceano_espiral.png",
            lines=[
                "Mientras navega hacia la isla, el océano gira en espiral.",
                "El Pollo emite pulsos de energía y se oscurece hasta volverse casi negro.",
            ],
        ),
    ]
    # Tras el 3er frasco el botiquín queda vacío -> arranca la Rotación 4 (Nivel 4).
    game.audio.play_music(settings.MUSIC_LEVEL_4)
    game.states.switch_to(CinematicScene(game, beats, on_finish=lambda: start_rotacion4_demo(game)))


# ======================================================================
# Rotación 4 (demo de la secuencia final) — La Isla
# ======================================================================

def start_rotacion4_demo(game) -> None:
    beat = build_botiquin_vacio_beat()
    game.states.switch_to(CinematicScene(game, [beat], on_finish=lambda: _go_to_isla_caminata(game)))


def _go_to_isla_caminata(game) -> None:
    _start_level(game, 4, on_complete=lambda: _go_to_cueva(game))


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