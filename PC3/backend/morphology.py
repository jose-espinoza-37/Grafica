"""
morphology.py
=============
Módulo de morfología matemática.
Aplica erosión, dilatación, apertura (opening) y cierre (closing)
sobre las máscaras binarias generadas por segmentation.py,
eliminando ruido residual y mejorando la forma de las regiones detectadas.
También calcula métricas sobre componentes conectados.

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


# ── Operaciones morfológicas básicas ────────────────────────────────────────

def get_kernel(size: int, shape: int = cv2.MORPH_ELLIPSE) -> np.ndarray:
    """
    Genera un elemento estructurante (kernel morfológico).

    Args:
        size: Tamaño del kernel (side length, preferiblemente impar).
        shape: Forma del kernel (MORPH_ELLIPSE, MORPH_RECT, MORPH_CROSS).

    Returns:
        Kernel como array NumPy uint8.
    """
    return cv2.getStructuringElement(shape, (size, size))


def apply_erosion(mask: np.ndarray,
                  kernel_size: int = 5,
                  iterations: int = 2) -> np.ndarray:
    """
    Erosión: elimina píxeles en los bordes de las regiones blancas.
    Útil para separar objetos cercanos y eliminar ruido puntual.

    Args:
        mask: Máscara binaria (uint8, valores 0 o 255).
        kernel_size: Tamaño del elemento estructurante.
        iterations: Número de veces que se aplica la erosión.

    Returns:
        Máscara erosionada.
    """
    kernel = get_kernel(kernel_size)
    return cv2.erode(mask, kernel, iterations=iterations)


def apply_dilation(mask: np.ndarray,
                   kernel_size: int = 5,
                   iterations: int = 2) -> np.ndarray:
    """
    Dilatación: expande los píxeles blancos hacia los bordes.
    Útil para rellenar pequeños huecos en regiones detectadas.

    Args:
        mask: Máscara binaria (uint8, valores 0 o 255).
        kernel_size: Tamaño del elemento estructurante.
        iterations: Número de veces que se aplica la dilatación.

    Returns:
        Máscara dilatada.
    """
    kernel = get_kernel(kernel_size)
    return cv2.dilate(mask, kernel, iterations=iterations)


def apply_opening(mask: np.ndarray, kernel_size: int = 7) -> np.ndarray:
    """
    Apertura (opening) = erosión seguida de dilatación.
    Elimina manchas pequeñas de ruido sin afectar las regiones grandes.

    Args:
        mask: Máscara binaria.
        kernel_size: Tamaño del kernel.

    Returns:
        Máscara con apertura aplicada.
    """
    kernel = get_kernel(kernel_size)
    return cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel)


def apply_closing(mask: np.ndarray, kernel_size: int = 9) -> np.ndarray:
    """
    Cierre (closing) = dilatación seguida de erosión.
    Rellena huecos pequeños dentro de las regiones detectadas.

    Args:
        mask: Máscara binaria.
        kernel_size: Tamaño del kernel.

    Returns:
        Máscara con cierre aplicado.
    """
    kernel = get_kernel(kernel_size)
    return cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel)


def apply_full_morphology(mask: np.ndarray, config: dict) -> dict:
    """
    Aplica la secuencia completa de operaciones morfológicas:
    apertura → cierre → erosión → dilatación.

    Args:
        mask: Máscara binaria bruta de segmentación.
        config: Configuración del proyecto.

    Returns:
        Diccionario con cada versión intermedia y la máscara final.
    """
    cfg = config["morphology"]

    opened  = apply_opening(mask,  kernel_size=cfg["opening_kernel"])
    closed  = apply_closing(opened, kernel_size=cfg["closing_kernel"])
    eroded  = apply_erosion(closed,
                            kernel_size=cfg["kernel_size"],
                            iterations=cfg["erosion_iterations"])
    dilated = apply_dilation(eroded,
                             kernel_size=cfg["kernel_size"],
                             iterations=cfg["dilation_iterations"])

    return {
        "raw_mask": mask,
        "opened":   opened,
        "closed":   closed,
        "eroded":   eroded,
        "final":    dilated,
    }


# ── Análisis de componentes conectados ──────────────────────────────────────

def analyze_connected_components(mask: np.ndarray,
                                  min_area: int = 100) -> dict:
    """
    Identifica manchas individuales (componentes conectados) en la máscara
    y calcula métricas como área, cantidad y porcentaje de infección.

    Args:
        mask: Máscara binaria final (después de morfología).
        min_area: Área mínima en píxeles para considerar una mancha válida.

    Returns:
        Diccionario con:
            'num_components'   - número de manchas válidas
            'total_area'       - área total de manchas (píxeles)
            'image_area'       - área total de la imagen (píxeles)
            'infection_ratio'  - porcentaje de área infectada
            'components'       - lista de dicts por componente
            'labeled_img'      - imagen con etiquetas de componentes
    """
    num_labels, labels, stats, centroids = cv2.connectedComponentsWithStats(
        mask, connectivity=8
    )

    image_area = mask.shape[0] * mask.shape[1]
    components = []
    total_area = 0

    # Label 0 = fondo, se omite
    for i in range(1, num_labels):
        area = int(stats[i, cv2.CC_STAT_AREA])
        if area < min_area:
            continue

        x    = int(stats[i, cv2.CC_STAT_LEFT])
        y    = int(stats[i, cv2.CC_STAT_TOP])
        w    = int(stats[i, cv2.CC_STAT_WIDTH])
        h    = int(stats[i, cv2.CC_STAT_HEIGHT])
        cx   = float(centroids[i][0])
        cy   = float(centroids[i][1])

        components.append({
            "id":       i,
            "area":     area,
            "bbox":     (x, y, w, h),
            "centroid": (cx, cy),
        })
        total_area += area

    return {
        "num_components":  len(components),
        "total_area":      total_area,
        "image_area":      image_area,
        "infection_ratio": round(total_area / image_area * 100, 2),
        "components":      components,
        "labeled_img":     labels.astype(np.int32),
    }


def draw_component_boxes(image: np.ndarray,
                          cc_result: dict) -> np.ndarray:
    """
    Dibuja bounding boxes alrededor de cada componente conectado
    sobre la imagen original.

    Args:
        image: Imagen BGR original.
        cc_result: Resultado de analyze_connected_components().

    Returns:
        Imagen BGR con bounding boxes dibujados.
    """
    annotated = image.copy()
    for comp in cc_result["components"]:
        x, y, w, h = comp["bbox"]
        cv2.rectangle(annotated, (x, y), (x + w, y + h),
                       color=(0, 0, 255), thickness=2)
        cv2.putText(annotated,
                    f"#{comp['id']} {comp['area']}px",
                    (x, max(y - 6, 10)),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.45, (0, 0, 200), 1, cv2.LINE_AA)
    return annotated


# ── Visualización ────────────────────────────────────────────────────────────

def plot_morphology_steps(morph_result: dict,
                           save_path: str = None) -> plt.Figure:
    """
    Muestra las 5 etapas morfológicas en una sola figura.

    Args:
        morph_result: Resultado de apply_full_morphology().
        save_path: Ruta para guardar (opcional).

    Returns:
        Objeto Figure de matplotlib.
    """
    steps = [
        ("Máscara raw",   morph_result["raw_mask"]),
        ("Apertura",      morph_result["opened"]),
        ("Cierre",        morph_result["closed"]),
        ("Erosión",       morph_result["eroded"]),
        ("Final (dilatada)", morph_result["final"]),
    ]

    fig, axes = plt.subplots(1, 5, figsize=(18, 4))
    for ax, (title, img) in zip(axes, steps):
        ax.imshow(img, cmap="Greens")
        ax.set_title(title, fontsize=10)
        ax.axis("off")

    plt.suptitle("Secuencia de operaciones morfológicas", fontsize=12)
    plt.tight_layout()

    if save_path:
        Path(save_path).parent.mkdir(parents=True, exist_ok=True)
        plt.savefig(save_path, dpi=150, bbox_inches="tight")
        print(f"[morphology] Pasos guardados en {save_path}")
    return fig


def plot_final_detection(original: np.ndarray,
                          annotated: np.ndarray,
                          cc_result: dict,
                          save_path: str = None) -> plt.Figure:
    """
    Figura final con imagen original y detección anotada.

    Args:
        original: Imagen BGR original.
        annotated: Imagen con bounding boxes.
        cc_result: Métricas de componentes conectados.
        save_path: Ruta para guardar (opcional).

    Returns:
        Objeto Figure de matplotlib.
    """
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 5))

    ax1.imshow(cv2.cvtColor(original, cv2.COLOR_BGR2RGB))
    ax1.set_title("Imagen original")
    ax1.axis("off")

    ax2.imshow(cv2.cvtColor(annotated, cv2.COLOR_BGR2RGB))
    ax2.set_title(
        f"Manchas detectadas: {cc_result['num_components']}\n"
        f"Área infectada: {cc_result['infection_ratio']:.1f}%"
    )
    ax2.axis("off")

    plt.suptitle("Detección final tras morfología + componentes conectados", fontsize=12)
    plt.tight_layout()

    if save_path:
        Path(save_path).parent.mkdir(parents=True, exist_ok=True)
        plt.savefig(save_path, dpi=150, bbox_inches="tight")
        print(f"[morphology] Detección final guardada en {save_path}")
    return fig


# ── Pipeline morfológico ─────────────────────────────────────────────────────

def run_morphology(mask: np.ndarray,
                   original_image: np.ndarray,
                   config: dict) -> dict:
    """
    Pipeline completo: morfología + análisis de componentes conectados.

    Args:
        mask: Máscara binaria de la segmentación K-means.
        original_image: Imagen BGR original (para anotaciones).
        config: Configuración del proyecto.

    Returns:
        Resultado combinado con máscara final, métricas y anotaciones.
    """
    morph_result = apply_full_morphology(mask, config)
    cc_result    = analyze_connected_components(morph_result["final"],
                                                 min_area=100)
    annotated    = draw_component_boxes(original_image, cc_result)

    return {
        "morph_steps":    morph_result,
        "final_mask":     morph_result["final"],
        "cc_metrics":     cc_result,
        "annotated_img":  annotated,
    }


# ── Ejemplo de uso ──────────────────────────────────────────────────────────
if __name__ == "__main__":
    import sys
    from segmentation import run_segmentation, identify_disease_cluster

    if len(sys.argv) < 2:
        print("Uso: python morphology.py <ruta_imagen>")
        sys.exit(1)

    config = load_config()
    img = cv2.imread(sys.argv[1])
    img = cv2.resize(img, tuple(config["preprocessing"]["image_size"]))

    # Obtener máscara de la segmentación
    seg_result   = run_segmentation(img, config)
    disease_idx  = seg_result["metrics"]["disease_cluster_idx"]
    raw_mask     = seg_result["cluster_masks"][disease_idx]

    result = run_morphology(raw_mask, img, config)
    cc     = result["cc_metrics"]

    print(f"\nMorfología aplicada correctamente.")
    print(f"Manchas individuales detectadas: {cc['num_components']}")
    print(f"Área infectada total: {cc['infection_ratio']:.2f}%")
    print(f"Área total en píxeles: {cc['total_area']}")

    plot_morphology_steps(result["morph_steps"],
                           save_path="outputs/segmented/morphology_steps.png")
    plot_final_detection(img, result["annotated_img"], cc,
                          save_path="outputs/segmented/final_detection.png")
    plt.show()
