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

    # Imagen de fondo del nivel (assets/backgrounds/nivelN.png). Se dibuja
    # estirada a pantalla completa, detrás de todo lo demás (tiles, enemigos,
    # jugador). Si es None, se usa el color plano settings.COLOR_BG de siempre.
    background_path: str | None = None

    # Nivel 3 (Bosque -> Playa): segundo fondo que reemplaza a background_path
    # apenas el jugador activa el checkpoint, siguiendo el lore (la transición
    # bosque/playa ocurre justo ahí). None en los niveles que no la necesitan.
    background_path_after_checkpoint: str | None = None

    # Igual que arriba pero para la música: si se define, reemplaza a
    # music_path en el mismo instante en que se activa el checkpoint (Nivel 3:
    # pista de bosque -> pista de playa). None en los niveles que no la necesitan.
    music_path_after_checkpoint: str | None = None

    # Si el nivel viene de un mapa de Tiled (ver systems/tilemap_loader.py),
    # aquí va el TilemapRenderer ya armado. Si es None, PlayScene sigue
    # dibujando los rectángulos de depuración de siempre (compatibilidad
    # con niveles armados a mano, como los de intro_flow.py).
    tilemap_renderer: object | None = None


class PlayScene(Scene):
    def __init__(self, game, player, config: LevelConfig, on_level_complete=None, level_factory=None) -> None:
        """
        level_factory: función sin argumentos que devuelve un LevelConfig
        nuevo (ej. _build_nivel1_config en intro_flow.py). Si se la pasa,
        PauseScene puede ofrecer "Reiniciar nivel" con un estado 100%
        limpio (enemigos vivos otra vez, ítems sin recoger, checkpoint
        desactivado). Si no se pasa, "Reiniciar nivel" solo manda al
        jugador de vuelta al punto de partida, sin resetear enemigos/ítems
        ya tocados - sigue siendo útil, solo menos completo.
        """
        self.game = game
        self.player = player
        self.config = config
        self.on_level_complete = on_level_complete
        self.level_factory = level_factory
        self.hud = HUD()

        self.camera = Camera(
            view_width=settings.BASE_WIDTH,
            view_height=settings.BASE_HEIGHT,
            level_width=config.level_width,
            level_height=config.level_height,
        )

        self._intro_timer = config.intro_autowalk_seconds
        self._completed = False

        # Fondo activo: arranca con background_path; cambia una sola vez a
        # background_path_after_checkpoint cuando el checkpoint se activa.
        self._current_bg_path = config.background_path
        self._bg_cache: dict[str, pygame.Surface] = {}

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

    def restart_level(self) -> None:
        """Llamado desde PauseScene ('Reiniciar nivel'). Ver nota de
        level_factory arriba sobre qué tan completo es el reinicio."""
        if self.level_factory is not None:
            self.config = self.level_factory()
            self.camera.level_width = self.config.level_width
            self.camera.level_height = self.config.level_height

        self._current_bg_path = self.config.background_path
        self.player.x, self.player.y = self.config.start_pos
        self.player.heal_full()
        self.camera.x, self.camera.y = 0.0, 0.0
        self._completed = False
        self._intro_timer = self.config.intro_autowalk_seconds

        if self._intro_timer > 0:
            self.game.input.set_scripted_input({"right": True})
        else:
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
            self.game.audio.play_sfx(settings.SFX_PAUSE)
            from src.scenes.pause_scene import PauseScene
            self.game.states.push(PauseScene(self.game, self))
            return

        self._update_gameplay(dt)

    def _update_gameplay(self, dt: float) -> None:
        solids = self._current_solids()
        gravity_scale = get_gravity_scale(self.player.rect, self.config.gravity_zones)
        self.player.update(dt, self.game.input, solids, gravity_scale=gravity_scale)

        for platform in self.config.cyclic_platforms:
            platform.update(dt)

        for pad in self.config.boost_pads:
            if pad.try_boost(self.player):
                self.game.audio.play_sfx(settings.SFX_BOOST)

        for item in self.config.powerup_items:
            if item.try_collect(self.player):
                if item.kind == item.KIND_DOUBLE_JUMP:
                    self.game.audio.play_sfx(settings.SFX_POWERUP_PLUMA)
                elif item.kind == item.KIND_DISGUISE:
                    self.game.audio.play_sfx(settings.SFX_POWERUP_PIO)

        if self.config.has_danger:
            self._update_enemies(dt)

        if self.config.checkpoint is not None:
            just_activated = self.config.checkpoint.update(dt, self.player.rect)
            if just_activated:
                self.game.audio.play_sfx(settings.SFX_CHECKPOINT)
                if self.config.background_path_after_checkpoint:
                    self._current_bg_path = self.config.background_path_after_checkpoint
                if self.config.music_path_after_checkpoint:
                    self.game.audio.play_music(self.config.music_path_after_checkpoint)

        if self.player.defeated:
            self._respawn_player()

        self.camera.update(dt, self.player.rect)

        if self.config.goal_rect and self.player.rect.colliderect(self.config.goal_rect):
            self._complete_level()

    def _update_enemies(self, dt: float) -> None:
        for enemy in self.config.enemies:
            enemy.update(dt)
            if enemy.alive and enemy.active and enemy.rect.colliderect(self.player.rect):
                if enemy.try_attack(self.player):
                    self.game.audio.play_sfx(settings.SFX_HIT_PLAYER)

        attack_rect = self.player.attack_rect
        if attack_rect is not None:
            for enemy in self.config.enemies:
                if enemy.alive and enemy.active and attack_rect.colliderect(enemy.rect):
                    enemy.take_damage()
                    self.game.audio.play_sfx(settings.SFX_HIT_ENEMY)
                    if not enemy.alive:
                        self.game.audio.play_sfx(settings.SFX_ENEMY_DEFEATED)

        self.config.enemies = [e for e in self.config.enemies if e.alive]

    def _respawn_player(self) -> None:
        if self.config.checkpoint is not None and self.config.checkpoint.activated:
            respawn_point = self.config.checkpoint.respawn_point
        else:
            respawn_point = self.config.start_pos
        self.player.respawn_at(respawn_point)

    def _draw_background(self, surface: pygame.Surface) -> None:
        """Dibuja la imagen de fondo del nivel, estirada a pantalla completa.
        Se cachea por ruta para no reescalar la imagen cada frame."""
        path = self._current_bg_path
        if not path:
            return
        size = surface.get_size()
        cache_key = f"{path}@{size}"
        bg = self._bg_cache.get(cache_key)
        if bg is None:
            raw = self.game.assets.get_image(path)
            bg = pygame.transform.scale(raw, size)
            self._bg_cache[cache_key] = bg
        surface.blit(bg, (0, 0))

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
            self.game.audio.play_sfx(settings.SFX_FRASCO)
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
        self._draw_background(surface)

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
            item.draw(surface, self.camera, self.game.assets)
        if self.config.checkpoint is not None:
            self.config.checkpoint.draw(surface, self.camera, self.game.assets)
        for enemy in self.config.enemies:
            enemy.draw(surface, self.camera, self.game.assets)

        self.player.draw(surface, self.camera, self.game.assets)

        if self.config.show_hud:
            self.hud.draw(surface, self.game.assets, self.player)