"""
tilemap_loader.py
--------------------
Carga niveles diseñados en Tiled (https://www.mapeditor.org/, gratis,
multiplataforma) y exportados como JSON ("File > Export As > JSON").
Convierte el mapa en:

  1. Un LevelConfig (play_scene.py) ya armado: sólidos de colisión + todas
     las entidades de Persona 2 (enemigos, checkpoint, power-ups, zonas de
     gravedad, boost pads, plataformas cíclicas) posicionadas según lo que
     se haya dibujado en Tiled.
  2. Un TilemapRenderer para dibujar las capas de tiles visuales. PlayScene
     lo usa automáticamente en vez de los rectángulos de depuración cuando
     se le pasa un nivel cargado con esta función.

======================================================================
CÓMO ARMAR UN NIVEL EN TILED (para quien diseñe los niveles del equipo)
======================================================================

1. Crear un tileset nuevo marcando "Embed tileset in map" — así todo
   queda en un solo archivo .json, sin un .tsx suelto que se pueda perder.
2. Usar el mismo tamaño de tile en todos los niveles (settings.TILE_SIZE,
   16 px por defecto).
3. Capas de TILES (Tile Layer):
     - Una o varias capas visuales, el nombre no importa (ej. "Fondo",
       "Tiles", "Decoracion"). Se dibujan en el orden en que aparecen.
     - Una capa llamada EXACTAMENTE "Colisiones": cualquier tile que no
       sea 0 ahí se convierte en un rectángulo sólido para la física.
       Esta capa nunca se dibuja (puede ser invisible en Tiled, no importa
       qué tile se use, solo importa si hay tile o no).
4. Capas de OBJETOS (Object Layer), nombres EXACTOS:
     - "Inicio": un objeto cualquiera; su posición (x, y) es el punto de
       partida del jugador.
     - "Meta": un objeto rectángulo; es la meta del nivel (goal_rect).
     - "Checkpoint": un objeto rectángulo; el punto de respawn a mitad
       de nivel.
     - "Enemigos": un objeto por enemigo. Propiedades personalizadas
       (panel "Custom Properties" de Tiled):
          is_mutant (bool), patrol_min_x (float), patrol_max_x (float),
          speed (float, opcional), reappear (bool, opcional),
          visible_time / hidden_time (float, solo si reappear = true)
     - "PowerUps": un objeto por ítem. Propiedad: kind = "double_jump" o
       "disguise".
     - "GravityZones": un objeto rectángulo por zona. Propiedad:
       gravity_scale (float).
     - "BoostPads": un objeto rectángulo por plataforma. Propiedad
       opcional: boost_velocity (float).
     - "CyclicPlatforms": un objeto rectángulo por plataforma.
       Propiedades opcionales: visible_time, hidden_time, start_visible (bool).
   Cualquier otra capa de objetos se ignora sin romper nada.

======================================================================
LIMITACIONES A PROPÓSITO (para no complicar el código en tiempo de jam)
======================================================================
- Solo se soportan tilesets EMBEBIDOS en el .json (no archivos .tsx/.tsj
  externos). Si Tiled exporta un tileset externo, hay que re-exportar
  marcando "Embed tileset in map".
- Las banderas de flip/rotación de tiles de Tiled se ignoran (el tile se
  dibuja siempre sin voltear). Avisen si hace falta soportarlo.
"""

from __future__ import annotations
from dataclasses import dataclass
import json
import os
import pygame

from src.core import settings
from src.scenes.play_scene import LevelConfig
from src.entities.checkpoint import Checkpoint
from src.entities.enemy import Enemy
from src.entities.gravity_zone import GravityZone
from src.entities.boost_pad import BoostPad
from src.entities.cyclic_platform import CyclicPlatform
from src.entities.cyclic_timer import CyclicTimer
from src.entities.powerup_item import PowerUpItem

GID_FLIP_MASK = 0x1FFFFFFF  # quita las banderas de flip de Tiled, nos quedamos solo con el id real


@dataclass
class _TileLayerData:
    name: str
    width: int
    height: int
    gids: list[int]


class Tileset:
    """Una imagen de tileset ya cortada en tiles individuales, indexada por gid global."""

    def __init__(
        self,
        assets,
        firstgid: int,
        image_path: str,
        tile_width: int,
        tile_height: int,
        columns: int,
        tile_count: int,
    ) -> None:
        self.firstgid = firstgid
        self.lastgid = firstgid + tile_count - 1

        atlas = assets.get_image(image_path)
        self._tiles: dict[int, pygame.Surface] = {}

        for local_id in range(tile_count):
            col = local_id % columns
            row = local_id // columns
            src_rect = pygame.Rect(col * tile_width, row * tile_height, tile_width, tile_height)
            tile_surface = pygame.Surface((tile_width, tile_height), pygame.SRCALPHA)
            tile_surface.blit(atlas, (0, 0), src_rect)
            self._tiles[firstgid + local_id] = tile_surface

    def contains(self, gid: int) -> bool:
        return self.firstgid <= gid <= self.lastgid

    def get_tile(self, gid: int) -> pygame.Surface | None:
        return self._tiles.get(gid)


class TilemapRenderer:
    """Dibuja las capas de tiles visuales (la capa 'Colisiones' nunca se dibuja, es invisible)."""

    def __init__(
        self,
        tilesets: list[Tileset],
        layers: list[_TileLayerData],
        tile_width: int,
        tile_height: int,
    ) -> None:
        self.tilesets = tilesets
        self.layers = layers
        self.tile_width = tile_width
        self.tile_height = tile_height

    def _tile_surface(self, gid: int) -> pygame.Surface | None:
        if gid == 0:
            return None
        gid = gid & GID_FLIP_MASK
        for tileset in self.tilesets:
            if tileset.contains(gid):
                return tileset.get_tile(gid)
        return None

    def draw(self, surface: pygame.Surface, camera) -> None:
        # Solo dibuja los tiles visibles en la cámara, para no recorrer
        # niveles enteros tile por tile si son grandes.
        view_left = max(0, int(camera.x) // self.tile_width)
        view_top = max(0, int(camera.y) // self.tile_height)
        view_right = int(camera.x + camera.view_width) // self.tile_width + 1
        view_bottom = int(camera.y + camera.view_height) // self.tile_height + 1

        for layer in self.layers:
            last_col = min(layer.width - 1, view_right)
            last_row = min(layer.height - 1, view_bottom)

            for row in range(view_top, last_row + 1):
                for col in range(view_left, last_col + 1):
                    gid = layer.gids[row * layer.width + col]
                    tile = self._tile_surface(gid)
                    if tile is None:
                        continue
                    world_rect = pygame.Rect(
                        col * self.tile_width, row * self.tile_height,
                        self.tile_width, self.tile_height,
                    )
                    surface.blit(tile, camera.apply(world_rect).topleft)


def _properties_dict(obj: dict) -> dict:
    return {p["name"]: p["value"] for p in obj.get("properties", [])}


def _object_rect(obj: dict) -> pygame.Rect:
    return pygame.Rect(
        round(obj["x"]), round(obj["y"]),
        round(obj.get("width", settings.TILE_SIZE)),
        round(obj.get("height", settings.TILE_SIZE)),
    )


def _build_solids_from_collision_layer(
    layer: _TileLayerData, tile_width: int, tile_height: int
) -> list[pygame.Rect]:
    """
    Combina tiles sólidos contiguos en la misma fila en un solo rectángulo,
    para no generar cientos de rects diminutos en niveles grandes (cada
    rect extra es una colisión más que revisar cada frame).
    """
    solids: list[pygame.Rect] = []

    for row in range(layer.height):
        col = 0
        while col < layer.width:
            if layer.gids[row * layer.width + col] == 0:
                col += 1
                continue
            run_start = col
            while col < layer.width and layer.gids[row * layer.width + col] != 0:
                col += 1
            run_length = col - run_start
            solids.append(pygame.Rect(
                run_start * tile_width, row * tile_height,
                run_length * tile_width, tile_height,
            ))

    return solids


def load_level(json_path: str, assets) -> tuple[LevelConfig, TilemapRenderer]:
    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    base_dir = os.path.dirname(json_path)
    tile_width = data["tilewidth"]
    tile_height = data["tileheight"]

    tilesets: list[Tileset] = []
    for ts in data["tilesets"]:
        if "image" not in ts:
            raise ValueError(
                f"El tileset '{ts.get('source', '?')}' es externo (.tsx/.tsj). "
                "Vuelve a exportar el mapa desde Tiled marcando 'Embed tileset in map'."
            )
        image_path = os.path.normpath(os.path.join(base_dir, ts["image"]))
        tilesets.append(Tileset(
            assets,
            firstgid=ts["firstgid"],
            image_path=image_path,
            tile_width=ts.get("tilewidth", tile_width),
            tile_height=ts.get("tileheight", tile_height),
            columns=ts["columns"],
            tile_count=ts["tilecount"],
        ))

    visual_layers: list[_TileLayerData] = []
    solids: list[pygame.Rect] = []

    enemies: list = []
    powerup_items: list = []
    gravity_zones: list = []
    boost_pads: list = []
    cyclic_platforms: list = []
    checkpoint = None
    goal_rect: pygame.Rect | None = None
    start_pos = (0.0, 0.0)

    for layer in data["layers"]:
        if layer["type"] == "tilelayer":
            tile_layer = _TileLayerData(layer["name"], layer["width"], layer["height"], layer["data"])
            if layer["name"] == "Colisiones":
                solids.extend(_build_solids_from_collision_layer(tile_layer, tile_width, tile_height))
            else:
                visual_layers.append(tile_layer)

        elif layer["type"] == "objectgroup":
            name = layer["name"]
            objects = layer.get("objects", [])

            if name == "Inicio" and objects:
                start_pos = (float(objects[0]["x"]), float(objects[0]["y"]))

            elif name == "Meta" and objects:
                goal_rect = _object_rect(objects[0])

            elif name == "Checkpoint" and objects:
                rect = _object_rect(objects[0])
                checkpoint = Checkpoint(rect.x, rect.y, rect.width, rect.height)

            elif name == "Enemigos":
                for obj in objects:
                    props = _properties_dict(obj)
                    rect = _object_rect(obj)
                    cyclic = None
                    if props.get("reappear"):
                        cyclic = CyclicTimer(
                            visible_time=float(props.get("visible_time", 2.0)),
                            hidden_time=float(props.get("hidden_time", 1.5)),
                        )
                    enemies.append(Enemy(
                        rect.x, rect.y, rect.width, rect.height,
                        patrol_min_x=props.get("patrol_min_x"),
                        patrol_max_x=props.get("patrol_max_x"),
                        speed=float(props.get("speed", settings.ENEMY_PATROL_SPEED)),
                        is_mutant=bool(props.get("is_mutant", True)),
                        reappear_cycle=cyclic,
                    ))

            elif name == "PowerUps":
                for obj in objects:
                    props = _properties_dict(obj)
                    rect = _object_rect(obj)
                    kind = props.get("kind", PowerUpItem.KIND_DOUBLE_JUMP)
                    powerup_items.append(PowerUpItem(rect.x, rect.y, kind, rect.width, rect.height))

            elif name == "GravityZones":
                for obj in objects:
                    props = _properties_dict(obj)
                    rect = _object_rect(obj)
                    gravity_zones.append(GravityZone(
                        rect.x, rect.y, rect.width, rect.height,
                        float(props.get("gravity_scale", 1.0)),
                    ))

            elif name == "BoostPads":
                for obj in objects:
                    props = _properties_dict(obj)
                    rect = _object_rect(obj)
                    raw_velocity = props.get("boost_velocity")
                    boost_pads.append(BoostPad(
                        rect.x, rect.y, rect.width, rect.height,
                        float(raw_velocity) if raw_velocity is not None else None,
                    ))

            elif name == "CyclicPlatforms":
                for obj in objects:
                    props = _properties_dict(obj)
                    rect = _object_rect(obj)
                    cyclic_platforms.append(CyclicPlatform(
                        rect.x, rect.y, rect.width, rect.height,
                        visible_time=float(props.get("visible_time", 2.0)),
                        hidden_time=float(props.get("hidden_time", 1.5)),
                        start_visible=bool(props.get("start_visible", True)),
                    ))

    config = LevelConfig(
        start_pos=start_pos,
        level_width=data["width"] * tile_width,
        level_height=data["height"] * tile_height,
        solids=solids,
        enemies=enemies,
        checkpoint=checkpoint,
        gravity_zones=gravity_zones,
        boost_pads=boost_pads,
        cyclic_platforms=cyclic_platforms,
        powerup_items=powerup_items,
        goal_rect=goal_rect,
    )

    renderer = TilemapRenderer(tilesets, visual_layers, tile_width, tile_height)
    return config, renderer
