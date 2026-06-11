"""
utils.py
========
Funciones auxiliares compartidas por los módulos de CNN, evaluación
y comparativa. Centraliza tareas comunes para no repetir código:

    - Carga de configuración (config.yaml)
    - Reproducibilidad (semillas)
    - Selección de dispositivo (CPU / GPU)
    - Lectura / escritura de JSON (con soporte para tipos NumPy)
    - Listado de imágenes
    - Conteo de parámetros de un modelo
    - Medición de tiempos de inferencia

Responsable: Henry Huanca
"""

import os
import json
import time
import random
from pathlib import Path
from contextlib import contextmanager

import numpy as np
import yaml
import torch


# ── Configuración ────────────────────────────────────────────────────────────

def load_config(config_path: str = "config.yaml") -> dict:
    """Carga los parámetros globales desde config.yaml."""
    with open(config_path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def get_section(config: dict, name: str, defaults: dict) -> dict:
    """
    Devuelve una sección de config combinada con valores por defecto.
    Permite que el proyecto funcione aunque config.yaml todavía no
    incluya las secciones 'cnn', 'training' o 'comparison'.

    Args:
        config: Diccionario de configuración completo.
        name: Nombre de la sección a leer (p. ej. 'cnn').
        defaults: Valores por defecto para esa sección.

    Returns:
        Diccionario con defaults sobreescritos por lo que haya en config.
    """
    section = dict(defaults)
    if config and isinstance(config.get(name), dict):
        section.update(config[name])
    return section


# ── Reproducibilidad y dispositivo ───────────────────────────────────────────

def set_seed(seed: int = 42) -> None:
    """Fija las semillas para que los experimentos sean reproducibles."""
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(seed)


def get_device(prefer_gpu: bool = True) -> torch.device:
    """Devuelve 'cuda' si hay GPU disponible, de lo contrario 'cpu'."""
    if prefer_gpu and torch.cuda.is_available():
        return torch.device("cuda")
    return torch.device("cpu")


# ── Archivos y carpetas ───────────────────────────────────────────────────────

def ensure_dir(path: str) -> Path:
    """Crea una carpeta (y sus padres) si no existe. Devuelve el Path."""
    p = Path(path)
    p.mkdir(parents=True, exist_ok=True)
    return p


def list_images(directory: str,
                extensions=(".jpg", ".jpeg", ".png")) -> list:
    """Lista, ordenadas, las rutas de imágenes dentro de una carpeta."""
    ext = {e.lower() for e in extensions}
    return sorted([
        p for p in Path(directory).iterdir()
        if p.is_file() and p.suffix.lower() in ext
    ])


# ── JSON con soporte para tipos NumPy / Torch ────────────────────────────────

class NumpyEncoder(json.JSONEncoder):
    """Codificador JSON que entiende arrays y escalares de NumPy."""
    def default(self, obj):
        if isinstance(obj, np.integer):
            return int(obj)
        if isinstance(obj, np.floating):
            return float(obj)
        if isinstance(obj, np.ndarray):
            return obj.tolist()
        return super().default(obj)


def save_json(data, output_path: str) -> None:
    """Guarda un objeto serializable en un archivo JSON con indentación."""
    ensure_dir(Path(output_path).parent)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False, cls=NumpyEncoder)
    print(f"[utils] JSON guardado en {output_path}")


def load_json(path: str):
    """Carga un archivo JSON."""
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


# ── Utilidades de modelo ──────────────────────────────────────────────────────

def count_parameters(model) -> tuple:
    """
    Cuenta parámetros totales y entrenables de un modelo de PyTorch.

    Returns:
        (total, entrenables)
    """
    total     = sum(p.numel() for p in model.parameters())
    trainable = sum(p.numel() for p in model.parameters() if p.requires_grad)
    return total, trainable


# ── Medición de tiempo ────────────────────────────────────────────────────────

@contextmanager
def timer(name: str = "bloque"):
    """Context manager simple para medir cuánto tarda un bloque de código."""
    start = time.perf_counter()
    yield
    print(f"[timer] {name}: {time.perf_counter() - start:.3f}s")


def measure_inference_time(fn, *args, n_warmup: int = 1, n_runs: int = 3, **kwargs):
    """
    Mide el tiempo medio (en milisegundos) de ejecutar una función.
    Útil para comparar la velocidad del pipeline clásico vs la CNN.

    Args:
        fn: Función a medir.
        n_warmup: Ejecuciones de calentamiento (no se promedian).
        n_runs: Ejecuciones que sí se promedian.

    Returns:
        (resultado_ultima_ejecucion, tiempo_medio_ms)
    """
    for _ in range(max(0, n_warmup)):
        fn(*args, **kwargs)

    times = []
    result = None
    for _ in range(max(1, n_runs)):
        start = time.perf_counter()
        result = fn(*args, **kwargs)
        times.append((time.perf_counter() - start) * 1000.0)

    return result, float(np.mean(times))