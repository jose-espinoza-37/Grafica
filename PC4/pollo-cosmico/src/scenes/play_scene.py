"""
play_scene.py
--------------
Escena de gameplay genérica. No tiene contenido de ningún nivel en
particular — recibe un LevelConfig ya armado (el diseño de cada nivel en
sí es trabajo en conjunto, ver intro_flow.py para un ejemplo completo) y
se encarga de:

  - Pasarle al Player los sólidos correctos cada frame (estáticos + las
    plataformas cíclicas que estén visibles en ese instante).
  - Actualizar enemigos, checkpoint, zonas de gravedad, boost pads,
    plataformas cíclicas e ítems de power-up.
  - Resolver el contacto jugador-enemigo en ambos sentidos (el enemigo
    lo golpea a él, su ataque los golpea a ellos).
  - Reaparecer al jugador en el checkpoint cuando es derrotado.
  - Detectar la meta del nivel: si el nivel tiene peligro, dispara la
    cutscene del frasco antes de continuar; si no (Nivel 4), continúa
    directo a lo que siga.
  - Pausa (acción "pause" -> apila PauseScene encima).
  - Auto-walk al entrar al nivel (intro_autowalk_seconds): el InputManager
    queda en modo scripteado caminando a la derecha por ese tiempo, y
    luego se le devuelve el control al jugador. Así se logra el efecto
    "el personaje camina solo y después controlas tú" sin necesitar
    ningún sistema de animación nuevo (ver cinematic_scene.py).
"""

from __future__ import annotations
from dataclasses import dataclass, field
import pygame

from src.core.scene_base import Scene
from src.core import settings
from src.systems.camera import Camera
from src.entities.gravity_zone import get_gravity_scale
from src.ui.hud import HUD


@dataclass
class LevelConfig:
    start_pos: tuple[float, float]
    level_width: int = settings.BASE_WIDTH
    level_height: int = settings.BASE_HEIGHT

    solids: list[pygame.Rect] = field(default_factory=list)
    enemies: list = field(default_factory=list)
    checkpoint: object | None = None
    gravity_zones: list = field(default_factory=list)
    boost_pads: list = field(default_factory=list)
    cyclic_platforms: list = field(default_factory=list)
    powerup_items: list = field(default_factory=list)
    goal_rect: pygame.Rect | None = None

    has_danger: bool = True             # False = Nivel 4 (solo caminar, sin frasco al final)
    show_frasco_dialogue: bool = False  # True solo en Nivel 1
    intro_autowalk_seconds: float = 0.0
    music_path: str | None = None
    show_hud: bool = True               # False para el tramo de caminata calma del Nivel 4

    # Si el nivel viene de un mapa de Tiled (ver systems/tilemap_loader.py),
    # aquí va el TilemapRenderer ya armado. Si es None, PlayScene sigue
    # dibujando los rectángulos de depuración de siempre (compatibilidad
    # con niveles armados a mano, como los de intro_flow.py).
    tilemap_renderer: object | None = None


class PlayScene(Scene):
    def __init__(self, game, player, config: LevelConfig, on_level_complete=None) -> None:
        self.game = game
        self.player = player
        self.config = config
        self.on_level_complete = on_level_complete
        self.hud = HUD()

        self.camera = Camera(
            view_width=settings.BASE_WIDTH,
            view_height=settings.BASE_HEIGHT,
            level_width=config.level_width,
            level_height=config.level_height,
        )

        self._intro_timer = config.intro_autowalk_seconds
        self._completed = False

    def on_enter(self) -> None:
        self.player.x, self.player.y = self.config.start_pos
        self.player.heal_full()
        self.camera.x, self.camera.y = 0.0, 0.0

        if self.config.music_path:
            self.game.audio.play_music(self.config.music_path)

        if self._intro_timer > 0:
            self.game.input.set_scripted_input({"right": True})

    def on_exit(self) -> None:
        self.game.input.clear_scripted_input()

    def handle_event(self, event: pygame.event.Event) -> None:
        pass

    def update(self, dt: float) -> None:
        if self._completed:
            return

        if self._intro_timer > 0:
            self._intro_timer -= dt
            if self._intro_timer <= 0:
                self.game.input.clear_scripted_input()

        if self.game.input.is_just_pressed("pause"):
            from src.scenes.pause_scene import PauseScene
            self.game.states.push(PauseScene(self.game))
            return

        self._update_gameplay(dt)

    def _update_gameplay(self, dt: float) -> None:
        solids = self._current_solids()
        gravity_scale = get_gravity_scale(self.player.rect, self.config.gravity_zones)
        self.player.update(dt, self.game.input, solids, gravity_scale=gravity_scale)

        for platform in self.config.cyclic_platforms:
            platform.update(dt)

        for pad in self.config.boost_pads:
            pad.try_boost(self.player)

        for item in self.config.powerup_items:
            item.try_collect(self.player)

        if self.config.has_danger:
            self._update_enemies(dt)

        if self.config.checkpoint is not None:
            self.config.checkpoint.check(self.player.rect)

        if self.player.defeated:
            self._respawn_player()

        self.camera.update(dt, self.player.rect)

        if self.config.goal_rect and self.player.rect.colliderect(self.config.goal_rect):
            self._complete_level()

    def _update_enemies(self, dt: float) -> None:
        for enemy in self.config.enemies:
            enemy.update(dt)
            if enemy.alive and enemy.active and enemy.rect.colliderect(self.player.rect):
                enemy.try_attack(self.player)

        attack_rect = self.player.attack_rect
        if attack_rect is not None:
            for enemy in self.config.enemies:
                if enemy.alive and enemy.active and attack_rect.colliderect(enemy.rect):
                    enemy.take_damage()

        self.config.enemies = [e for e in self.config.enemies if e.alive]

    def _respawn_player(self) -> None:
        if self.config.checkpoint is not None and self.config.checkpoint.activated:
            respawn_point = self.config.checkpoint.respawn_point
        else:
            respawn_point = self.config.start_pos
        self.player.respawn_at(respawn_point)

    def _current_solids(self) -> list[pygame.Rect]:
        solids = list(self.config.solids)
        for platform in self.config.cyclic_platforms:
            rect = platform.solid_rect
            if rect is not None:
                solids.append(rect)
        return solids

    def _complete_level(self) -> None:
        self._completed = True

        if self.config.has_danger:
            from src.scenes.cinematic_scene import CinematicScene, build_frasco_beat
            self.player.heal_full()
            beat = build_frasco_beat(self.config.show_frasco_dialogue)

            def _continue() -> None:
                if self.on_level_complete:
                    self.on_level_complete()

            self.game.states.switch_to(CinematicScene(self.game, [beat], on_finish=_continue))
        else:
            if self.on_level_complete:
                self.on_level_complete()

    def draw(self, surface: pygame.Surface) -> None:
        surface.fill(settings.COLOR_BG)

        if self.config.tilemap_renderer is not None:
            self.config.tilemap_renderer.draw(surface, self.camera)
        else:
            for solid in self._current_solids():
                pygame.draw.rect(surface, settings.COLOR_DEBUG_SOLID, self.camera.apply(solid))

        for zone in self.config.gravity_zones:
            zone.draw(surface, self.camera)
        for pad in self.config.boost_pads:
            pad.draw(surface, self.camera)
        for item in self.config.powerup_items:
            item.draw(surface, self.camera)
        if self.config.checkpoint is not None:
            self.config.checkpoint.draw(surface, self.camera)
        for enemy in self.config.enemies:
            enemy.draw(surface, self.camera)

        self.player.draw(surface, self.camera)

        if self.config.show_hud:
            self.hud.draw(surface, self.game.assets, self.player)
