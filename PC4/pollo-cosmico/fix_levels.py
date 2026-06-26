#!/usr/bin/env python3
"""
fix_levels.py  — Ejecutar UNA VEZ desde la raíz del proyecto:
    python fix_levels.py

Qué hace:
  Expande verticalmente nivel_1.json y nivel_2.json de modo que el mundo
  tenga al menos 368 px de alto (>= BASE_HEIGHT=360), bajando todo el
  contenido (tiles, objetos) hacia las filas inferiores para que el piso
  quede abajo de verdad en lugar de flotar en el centro de la pantalla.

  Hace backup automático (.bak) antes de sobreescribir.
"""
import json, copy, shutil, os

NEW_H      = 23          # 23 * 16 = 368 px  >=  360 px (BASE_HEIGHT)
TILE       = 16
LEVELS_DIR = "assets/levels"


def shift_tile_data(data: list, old_w: int, old_h: int, new_h: int) -> list:
    """Rellena con filas vacías ARRIBA para que el contenido original quede
    en las mismas filas relativas al fondo del mapa."""
    extra = new_h - old_h
    return [0] * (extra * old_w) + list(data)


def shift_objects(objects: list, old_h: int, new_h: int) -> list:
    dy = (new_h - old_h) * TILE
    result = []
    for obj in objects:
        o = copy.deepcopy(obj)
        o["y"] = o["y"] + dy
        result.append(o)
    return result


def rebuild(filename: str) -> None:
    path = os.path.join(LEVELS_DIR, filename)
    if not os.path.exists(path):
        print(f"  {filename}: NO encontrado en {LEVELS_DIR}, saltando.")
        return

    bak = path + ".bak"
    shutil.copy2(path, bak)
    print(f"  Backup → {bak}")

    with open(path, encoding="utf-8") as f:
        data = json.load(f)

    old_h = data["height"]
    old_w = data["width"]

    if old_h >= NEW_H:
        print(f"  {filename}: ya tiene height={old_h} >= {NEW_H}, nada que hacer.")
        return

    data["height"] = NEW_H

    for layer in data["layers"]:
        if layer["type"] == "tilelayer":
            layer["height"] = NEW_H
            layer["data"]   = shift_tile_data(layer["data"], old_w, old_h, NEW_H)
            expected = old_w * NEW_H
            actual   = len(layer["data"])
            if actual != expected:
                raise AssertionError(
                    f"ERROR en capa '{layer['name']}': "
                    f"len={actual}, esperado={expected}"
                )
        elif layer["type"] == "objectgroup":
            layer["objects"] = shift_objects(layer["objects"], old_h, NEW_H)

    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)

    print(
        f"  {filename}: height {old_h}→{NEW_H}  "
        f"({old_h*TILE}→{NEW_H*TILE} px)  ✓"
    )


if __name__ == "__main__":
    print("=== fix_levels.py ===")
    rebuild("nivel_1.json")
    rebuild("nivel_2.json")
    rebuild("nivel_3.json")
    rebuild("nivel_4.json")
    print("\nListo. Si quieres revertir, copia los .bak de vuelta sobre los .json.")
