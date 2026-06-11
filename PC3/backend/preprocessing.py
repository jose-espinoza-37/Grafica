"""
preprocessing.py
================
Módulo de preprocesamiento de imágenes.
Aplica filtros pasa bajos (Gaussian Blur, suavizado),
filtros pasa altos (realce de bordes) y normalización.

Responsable: Jose Espinoza
"""

import cv2
import numpy as np
import yaml
from pathlib import Path


def load_config(config_path: str = "config.yaml") -> dict:
    """Carga los parámetros globales desde config.yaml."""
    with open(config_path, "r") as f:
        return yaml.safe_load(f)


def load_image(image_path: str) -> np.ndarray:
    """
    Carga una imagen desde disco en formato BGR (OpenCV).

    Args:
        image_path: Ruta a la imagen.

    Returns:
        Imagen como array NumPy en BGR.

    Raises:
        FileNotFoundError: Si la imagen no existe.
    """
    path = Path(image_path)
    if not path.exists():
        raise FileNotFoundError(f"No se encontró la imagen: {image_path}")
    img = cv2.imread(str(path))
    if img is None:
        raise ValueError(f"No se pudo leer la imagen: {image_path}")
    return img


def resize_image(image: np.ndarray, size: tuple = (256, 256)) -> np.ndarray:
    """
    Redimensiona la imagen al tamaño objetivo.

    Args:
        image: Imagen BGR.
        size: Tupla (ancho, alto).

    Returns:
        Imagen redimensionada.
    """
    return cv2.resize(image, size, interpolation=cv2.INTER_AREA)


def apply_gaussian_blur(image: np.ndarray,
                        kernel_size: int = 5,
                        sigma: float = 1.0) -> np.ndarray:
    """
    Aplica filtro pasa bajo con Gaussian Blur.
    Reduce ruido de alta frecuencia manteniendo la estructura general.

    Args:
        image: Imagen BGR.
        kernel_size: Tamaño del kernel (debe ser impar).
        sigma: Desviación estándar del kernel Gaussiano.

    Returns:
        Imagen suavizada.
    """
    if kernel_size % 2 == 0:
        kernel_size += 1  # Asegurar que sea impar
    return cv2.GaussianBlur(image, (kernel_size, kernel_size), sigma)


def apply_median_blur(image: np.ndarray, kernel_size: int = 5) -> np.ndarray:
    """
    Aplica filtro de mediana (útil para ruido sal-y-pimienta).

    Args:
        image: Imagen BGR.
        kernel_size: Tamaño del kernel (debe ser impar).

    Returns:
        Imagen filtrada.
    """
    if kernel_size % 2 == 0:
        kernel_size += 1
    return cv2.medianBlur(image, kernel_size)


def apply_highpass_filter(image: np.ndarray,
                          alpha: float = 1.5) -> np.ndarray:
    """
    Aplica filtro pasa alto para realzar bordes y texturas.
    Técnica: imagen original - versión suavizada = detalles de alta frecuencia.
    Luego se suma a la original ponderado por alpha (unsharp masking).

    Args:
        image: Imagen BGR.
        alpha: Factor de realce (>1 aumenta nitidez).

    Returns:
        Imagen con bordes realzados.
    """
    blurred = cv2.GaussianBlur(image, (9, 9), 0)
    high_freq = cv2.subtract(image, blurred)
    sharpened = cv2.addWeighted(image, 1.0, high_freq, alpha, 0)
    return np.clip(sharpened, 0, 255).astype(np.uint8)


def apply_edge_detection(image: np.ndarray,
                         method: str = "canny") -> np.ndarray:
    """
    Detecta bordes en la imagen (escala de grises).

    Args:
        image: Imagen BGR.
        method: 'canny' | 'sobel' | 'laplacian'

    Returns:
        Imagen de bordes en escala de grises.
    """
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

    if method == "canny":
        edges = cv2.Canny(gray, threshold1=50, threshold2=150)
    elif method == "sobel":
        sobelx = cv2.Sobel(gray, cv2.CV_64F, 1, 0, ksize=3)
        sobely = cv2.Sobel(gray, cv2.CV_64F, 0, 1, ksize=3)
        edges = cv2.magnitude(sobelx, sobely)
        edges = np.uint8(np.clip(edges, 0, 255))
    elif method == "laplacian":
        edges = cv2.Laplacian(gray, cv2.CV_64F)
        edges = np.uint8(np.abs(edges))
    else:
        raise ValueError(f"Método de detección no reconocido: {method}")

    return edges


def normalize_image(image: np.ndarray,
                    mean: list = None,
                    std: list = None) -> np.ndarray:
    """
    Normaliza la imagen al rango [0, 1] y aplica media/std por canal.
    Útil para alimentar modelos CNN.

    Args:
        image: Imagen BGR uint8.
        mean: Lista de 3 valores de media por canal (BGR orden invertido).
        std: Lista de 3 valores de desviación estándar por canal.

    Returns:
        Imagen normalizada como float32.
    """
    img_float = image.astype(np.float32) / 255.0

    if mean is not None and std is not None:
        # Convertir de BGR a RGB para aplicar stats ImageNet
        img_rgb = img_float[:, :, ::-1]
        mean_arr = np.array(mean, dtype=np.float32)
        std_arr  = np.array(std,  dtype=np.float32)
        img_norm = (img_rgb - mean_arr) / std_arr
        return img_norm

    return img_float


def preprocess_pipeline(image_path: str,
                        config: dict = None) -> dict:
    """
    Pipeline completo de preprocesamiento para una imagen.
    Devuelve un diccionario con todas las versiones procesadas.

    Args:
        image_path: Ruta a la imagen original.
        config: Diccionario de configuración (si None, carga config.yaml).

    Returns:
        Diccionario con claves:
            'original'   - imagen BGR original redimensionada
            'blurred'    - imagen con Gaussian Blur
            'sharpened'  - imagen con filtro pasa alto
            'edges'      - detección de bordes Canny
            'normalized' - imagen normalizada float32
    """
    if config is None:
        config = load_config()

    cfg_pre = config["preprocessing"]
    size    = tuple(cfg_pre["image_size"])

    # 1. Cargar y redimensionar
    img = load_image(image_path)
    img = resize_image(img, size)

    # 2. Filtro pasa bajo
    blurred = apply_gaussian_blur(
        img,
        kernel_size=cfg_pre["gaussian_blur_kernel"],
        sigma=cfg_pre["gaussian_blur_sigma"]
    )

    # 3. Filtro pasa alto
    sharpened = apply_highpass_filter(
        img,
        alpha=cfg_pre["sharpen_alpha"]
    )

    # 4. Detección de bordes
    edges = apply_edge_detection(img, method="canny")

    # 5. Normalización
    normalized = normalize_image(
        img,
        mean=cfg_pre["normalize_mean"],
        std=cfg_pre["normalize_std"]
    )

    return {
        "original":   img,
        "blurred":    blurred,
        "sharpened":  sharpened,
        "edges":      edges,
        "normalized": normalized,
    }


def save_preprocessed(results: dict, output_dir: str, filename: str) -> None:
    """
    Guarda todas las versiones preprocesadas en disco.

    Args:
        results: Diccionario devuelto por preprocess_pipeline().
        output_dir: Carpeta destino.
        filename: Nombre base del archivo (sin extensión).
    """
    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)

    cv2.imwrite(str(out / f"{filename}_original.jpg"),   results["original"])
    cv2.imwrite(str(out / f"{filename}_blurred.jpg"),    results["blurred"])
    cv2.imwrite(str(out / f"{filename}_sharpened.jpg"),  results["sharpened"])
    cv2.imwrite(str(out / f"{filename}_edges.jpg"),      results["edges"])
    # La imagen normalizada se guarda escalada a [0,255] para visualización
    norm_vis = (results["normalized"] * 255).clip(0, 255).astype(np.uint8)
    cv2.imwrite(str(out / f"{filename}_normalized.jpg"), norm_vis)
    print(f"[preprocessing] Guardadas versiones de '{filename}' en {output_dir}")


# ── Ejemplo de uso ──────────────────────────────────────────────────────────
if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("Uso: python preprocessing.py <ruta_imagen>")
        sys.exit(1)

    config = load_config()
    results = preprocess_pipeline(sys.argv[1], config)

    print("Versiones generadas:", list(results.keys()))
    print("Tamaño imagen original:", results["original"].shape)

    save_preprocessed(results, config["paths"]["data_processed"], "prueba")
