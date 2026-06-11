"""
color_analysis.py
=================
Módulo de análisis de color e histogramas.
Analiza la distribución de colores en espacios RGB y HSV
para identificar zonas con cambios cromáticos asociados a enfermedades
(amarillo, marrón, necrótico).

Responsable: Jose Espinoza
"""

import cv2
import numpy as np
import matplotlib.pyplot as plt
import yaml
from pathlib import Path


def load_config(config_path: str = "config.yaml") -> dict:
    with open(config_path, "r") as f:
        return yaml.safe_load(f)


# ── Conversión de espacios de color ─────────────────────────────────────────

def bgr_to_rgb(image: np.ndarray) -> np.ndarray:
    """Convierte imagen de BGR (OpenCV) a RGB."""
    return cv2.cvtColor(image, cv2.COLOR_BGR2RGB)


def bgr_to_hsv(image: np.ndarray) -> np.ndarray:
    """
    Convierte imagen BGR a HSV.
    En OpenCV: H ∈ [0,180], S ∈ [0,255], V ∈ [0,255]
    """
    return cv2.cvtColor(image, cv2.COLOR_BGR2HSV)


def bgr_to_lab(image: np.ndarray) -> np.ndarray:
    """Convierte a espacio L*a*b* (útil para distancias perceptuales)."""
    return cv2.cvtColor(image, cv2.COLOR_BGR2Lab)


# ── Histogramas ─────────────────────────────────────────────────────────────

def compute_rgb_histograms(image: np.ndarray,
                           bins: int = 64) -> dict:
    """
    Calcula histogramas por canal R, G, B.

    Args:
        image: Imagen BGR.
        bins: Número de bins.

    Returns:
        Diccionario con claves 'R', 'G', 'B', cada uno con arrays (hist, bin_edges).
    """
    img_rgb = bgr_to_rgb(image)
    histograms = {}
    for i, channel in enumerate(["R", "G", "B"]):
        hist, edges = np.histogram(
            img_rgb[:, :, i].ravel(),
            bins=bins,
            range=(0, 256)
        )
        histograms[channel] = {"hist": hist, "edges": edges}
    return histograms


def compute_hsv_histograms(image: np.ndarray,
                           hue_bins: int = 36,
                           sat_bins: int = 32,
                           val_bins: int = 32) -> dict:
    """
    Calcula histogramas por canal H, S, V.

    Args:
        image: Imagen BGR.
        hue_bins: Bins para Hue (0-180 en OpenCV).
        sat_bins: Bins para Saturación (0-255).
        val_bins: Bins para Value/Brillo (0-255).

    Returns:
        Diccionario con claves 'H', 'S', 'V'.
    """
    img_hsv = bgr_to_hsv(image)
    ranges = {"H": (0, 181), "S": (0, 256), "V": (0, 256)}
    bin_counts = {"H": hue_bins, "S": sat_bins, "V": val_bins}

    histograms = {}
    for i, channel in enumerate(["H", "S", "V"]):
        hist, edges = np.histogram(
            img_hsv[:, :, i].ravel(),
            bins=bin_counts[channel],
            range=ranges[channel]
        )
        histograms[channel] = {"hist": hist, "edges": edges}
    return histograms


# ── Análisis de zonas enfermas ───────────────────────────────────────────────

def detect_disease_zones_by_color(image: np.ndarray,
                                   config: dict) -> dict:
    """
    Detecta píxeles correspondientes a zonas enfermas basándose
    en rangos de color HSV (amarillo, marrón, necrótico).

    Args:
        image: Imagen BGR.
        config: Configuración del proyecto.

    Returns:
        Diccionario con:
            'mask'            - máscara binaria de zona enferma
            'overlay'         - imagen original con zona marcada en rojo
            'disease_ratio'   - porcentaje de píxeles enfermos (0-100)
    """
    cfg = config["segmentation"]
    img_hsv = bgr_to_hsv(image)

    lower = np.array([cfg["disease_hue_min"],
                      cfg["disease_sat_min"],
                      cfg["disease_val_min"]], dtype=np.uint8)
    upper = np.array([cfg["disease_hue_max"], 255, 255], dtype=np.uint8)

    mask = cv2.inRange(img_hsv, lower, upper)

    # Overlay: regiones enfermas marcadas en rojo sobre la imagen original
    overlay = image.copy()
    overlay[mask > 0] = [0, 0, 200]  # BGR rojo

    total_pixels   = image.shape[0] * image.shape[1]
    disease_pixels = int(np.sum(mask > 0))
    disease_ratio  = round(disease_pixels / total_pixels * 100, 2)

    return {
        "mask": mask,
        "overlay": overlay,
        "disease_ratio": disease_ratio,
        "disease_pixels": disease_pixels,
        "total_pixels": total_pixels,
    }


def compute_color_statistics(image: np.ndarray) -> dict:
    """
    Calcula estadísticas de color: media y desviación estándar
    por canal en RGB y HSV.

    Args:
        image: Imagen BGR.

    Returns:
        Diccionario con medias y std en ambos espacios de color.
    """
    img_rgb = bgr_to_rgb(image)
    img_hsv = bgr_to_hsv(image)

    stats = {}
    for i, ch in enumerate(["R", "G", "B"]):
        stats[f"rgb_{ch}_mean"] = float(np.mean(img_rgb[:, :, i]))
        stats[f"rgb_{ch}_std"]  = float(np.std(img_rgb[:, :, i]))

    for i, ch in enumerate(["H", "S", "V"]):
        stats[f"hsv_{ch}_mean"] = float(np.mean(img_hsv[:, :, i]))
        stats[f"hsv_{ch}_std"]  = float(np.std(img_hsv[:, :, i]))

    return stats


# ── Visualización ────────────────────────────────────────────────────────────

def plot_rgb_histograms(image: np.ndarray,
                        title: str = "Histogramas RGB",
                        save_path: str = None) -> plt.Figure:
    """
    Grafica los histogramas R, G, B de una imagen.

    Args:
        image: Imagen BGR.
        title: Título de la figura.
        save_path: Ruta para guardar (opcional).

    Returns:
        Objeto Figure de matplotlib.
    """
    hists = compute_rgb_histograms(image)
    colors = {"R": "red", "G": "green", "B": "blue"}

    fig, axes = plt.subplots(1, 3, figsize=(14, 4))
    fig.suptitle(title, fontsize=13)

    for ax, (channel, data) in zip(axes, hists.items()):
        centers = (data["edges"][:-1] + data["edges"][1:]) / 2
        ax.bar(centers, data["hist"], width=4,
               color=colors[channel], alpha=0.75, edgecolor="none")
        ax.set_title(f"Canal {channel}")
        ax.set_xlabel("Intensidad (0-255)")
        ax.set_ylabel("Frecuencia")
        ax.set_xlim(0, 255)

    plt.tight_layout()
    if save_path:
        Path(save_path).parent.mkdir(parents=True, exist_ok=True)
        plt.savefig(save_path, dpi=150, bbox_inches="tight")
        print(f"[color_analysis] Histograma RGB guardado en {save_path}")
    return fig


def plot_hsv_histograms(image: np.ndarray,
                        title: str = "Histogramas HSV",
                        save_path: str = None) -> plt.Figure:
    """
    Grafica los histogramas H, S, V de una imagen con colores indicativos.

    Args:
        image: Imagen BGR.
        title: Título de la figura.
        save_path: Ruta para guardar (opcional).

    Returns:
        Objeto Figure de matplotlib.
    """
    cfg_default = {"hue_bins": 36, "sat_bins": 32, "val_bins": 32}
    hists = compute_hsv_histograms(image,
                                   hue_bins=cfg_default["hue_bins"],
                                   sat_bins=cfg_default["sat_bins"],
                                   val_bins=cfg_default["val_bins"])
    channel_colors = {"H": "darkorange", "S": "mediumpurple", "V": "steelblue"}
    xlabels = {"H": "Hue (0-180)", "S": "Saturación (0-255)", "V": "Brillo (0-255)"}

    fig, axes = plt.subplots(1, 3, figsize=(14, 4))
    fig.suptitle(title, fontsize=13)

    for ax, (channel, data) in zip(axes, hists.items()):
        centers = (data["edges"][:-1] + data["edges"][1:]) / 2
        ax.bar(centers, data["hist"], width=centers[1] - centers[0],
               color=channel_colors[channel], alpha=0.80, edgecolor="none")
        ax.set_title(f"Canal {channel}")
        ax.set_xlabel(xlabels[channel])
        ax.set_ylabel("Frecuencia")

    plt.tight_layout()
    if save_path:
        Path(save_path).parent.mkdir(parents=True, exist_ok=True)
        plt.savefig(save_path, dpi=150, bbox_inches="tight")
        print(f"[color_analysis] Histograma HSV guardado en {save_path}")
    return fig


def plot_comparison(original: np.ndarray,
                    overlay: np.ndarray,
                    disease_ratio: float,
                    save_path: str = None) -> plt.Figure:
    """
    Muestra la imagen original junto al overlay de zonas enfermas.

    Args:
        original: Imagen BGR original.
        overlay: Imagen BGR con overlay de enfermedad.
        disease_ratio: Porcentaje de área enferma.
        save_path: Ruta para guardar (opcional).

    Returns:
        Objeto Figure de matplotlib.
    """
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(10, 5))

    ax1.imshow(bgr_to_rgb(original))
    ax1.set_title("Imagen original")
    ax1.axis("off")

    ax2.imshow(bgr_to_rgb(overlay))
    ax2.set_title(f"Zona enferma detectada ({disease_ratio:.1f}%)")
    ax2.axis("off")

    plt.suptitle("Análisis de color — detección por HSV", fontsize=12)
    plt.tight_layout()

    if save_path:
        Path(save_path).parent.mkdir(parents=True, exist_ok=True)
        plt.savefig(save_path, dpi=150, bbox_inches="tight")
        print(f"[color_analysis] Comparación guardada en {save_path}")
    return fig


# ── Función principal de análisis ───────────────────────────────────────────

def analyze_image(image: np.ndarray, config: dict) -> dict:
    """
    Análisis completo de color de una imagen.

    Args:
        image: Imagen BGR (ya preprocesada).
        config: Configuración del proyecto.

    Returns:
        Diccionario con histogramas, estadísticas y detección de zonas enfermas.
    """
    cfg_ca = config["color_analysis"]

    rgb_hists  = compute_rgb_histograms(image, bins=cfg_ca["rgb_bins"])
    hsv_hists  = compute_hsv_histograms(image,
                                        hue_bins=cfg_ca["hsv_hue_bins"],
                                        sat_bins=cfg_ca["hsv_sat_bins"],
                                        val_bins=cfg_ca["hsv_val_bins"])
    stats      = compute_color_statistics(image)
    disease    = detect_disease_zones_by_color(image, config)

    return {
        "rgb_histograms":  rgb_hists,
        "hsv_histograms":  hsv_hists,
        "color_stats":     stats,
        "disease_mask":    disease["mask"],
        "disease_overlay": disease["overlay"],
        "disease_ratio":   disease["disease_ratio"],
    }


# ── Ejemplo de uso ──────────────────────────────────────────────────────────
if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("Uso: python color_analysis.py <ruta_imagen>")
        sys.exit(1)

    config = load_config()
    img = cv2.imread(sys.argv[1])
    img = cv2.resize(img, tuple(config["preprocessing"]["image_size"]))

    results = analyze_image(img, config)

    print(f"Porcentaje área enferma: {results['disease_ratio']}%")
    print("Estadísticas de color:")
    for k, v in results["color_stats"].items():
        print(f"  {k}: {v:.2f}")

    plot_rgb_histograms(img, save_path="outputs/metrics/hist_rgb.png")
    plot_hsv_histograms(img, save_path="outputs/metrics/hist_hsv.png")
    plot_comparison(img, results["disease_overlay"],
                    results["disease_ratio"],
                    save_path="outputs/segmented/color_detection.png")
    plt.show()
