"""
segmentation.py
===============
Módulo de segmentación sin supervisión mediante K-means en espacio HSV.
No utiliza etiquetas: el algoritmo descubre automáticamente las regiones
de la hoja (sana, enferma, fondo) agrupando píxeles por color.

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


# ── K-means en espacio HSV ───────────────────────────────────────────────────

def segment_kmeans_hsv(image: np.ndarray,
                       k: int = 3,
                       max_iter: int = 100,
                       attempts: int = 5) -> dict:
    """
    Aplica K-means sobre los valores HSV de cada píxel.
    Al trabajar en HSV se logra mayor separación entre zonas
    enfermas (amarillo/marrón) y hojas sanas (verde).

    Args:
        image: Imagen BGR.
        k: Número de clusters.
        max_iter: Iteraciones máximas del algoritmo.
        attempts: Intentos con distintas inicializaciones (se elige el mejor).

    Returns:
        Diccionario con:
            'labels'        - etiqueta de cluster por píxel (H x W)
            'centers'       - centros de cluster en espacio HSV (k x 3)
            'segmented_img' - imagen coloreada por cluster
            'cluster_masks' - lista de k máscaras binarias (una por cluster)
    """
    img_hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)

    # Aplanar a (N_píxeles, 3) y convertir a float32
    h, w    = img_hsv.shape[:2]
    pixels  = img_hsv.reshape(-1, 3).astype(np.float32)

    # Criterio de parada: máx iteraciones o epsilon de convergencia
    criteria = (
        cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER,
        max_iter,
        0.2
    )

    _, labels, centers = cv2.kmeans(
        pixels,
        k,
        None,
        criteria,
        attempts,
        cv2.KMEANS_PP_CENTERS  # Inicialización K-means++ (más estable)
    )

    labels  = labels.flatten().reshape(h, w)
    centers = centers.astype(np.uint8)

    # Imagen coloreada: cada cluster recibe el color de su centro en HSV
    segmented_hsv = centers[labels]
    segmented_img = cv2.cvtColor(segmented_hsv, cv2.COLOR_HSV2BGR)

    # Máscaras binarias individuales por cluster
    cluster_masks = [
        (labels == i).astype(np.uint8) * 255
        for i in range(k)
    ]

    return {
        "labels":        labels,
        "centers":       centers,
        "segmented_img": segmented_img,
        "cluster_masks": cluster_masks,
    }


def identify_disease_cluster(centers: np.ndarray) -> int:
    """
    Identifica automáticamente cuál cluster corresponde a zona enferma.
    Criterio: el cluster con mayor valor de Hue dentro del rango
    amarillo-marrón (H ≈ 15-35 en OpenCV) y alta saturación.

    Args:
        centers: Array (k, 3) con centros HSV de cada cluster.

    Returns:
        Índice del cluster más probable de representar enfermedad.
    """
    disease_hue_center = 25.0  # Centro del rango amarillo-marrón
    scores = []

    for center in centers:
        hue, sat, val = float(center[0]), float(center[1]), float(center[2])
        # Penalizar por distancia al hue de enfermedad y recompensar saturación
        hue_distance = abs(hue - disease_hue_center)
        score = sat - hue_distance * 2  # Score heurístico
        scores.append(score)

    return int(np.argmax(scores))


def compute_cluster_metrics(labels: np.ndarray,
                             centers: np.ndarray,
                             disease_cluster_idx: int) -> dict:
    """
    Calcula métricas sobre los clusters detectados.

    Args:
        labels: Mapa de etiquetas (H x W).
        centers: Centros HSV de cada cluster.
        disease_cluster_idx: Índice del cluster de enfermedad.

    Returns:
        Diccionario con métricas por cluster y totales.
    """
    h, w         = labels.shape
    total_pixels = h * w

    metrics = {
        "total_pixels": total_pixels,
        "clusters": [],
        "disease_cluster_idx": disease_cluster_idx,
        "disease_ratio": 0.0,
    }

    for i, center in enumerate(centers):
        count = int(np.sum(labels == i))
        ratio = round(count / total_pixels * 100, 2)
        metrics["clusters"].append({
            "id": i,
            "pixel_count": count,
            "percentage": ratio,
            "hsv_center": center.tolist(),
            "is_disease": i == disease_cluster_idx,
        })
        if i == disease_cluster_idx:
            metrics["disease_ratio"] = ratio

    return metrics


# ── Segmentación por umbral HSV (complementaria a K-means) ──────────────────

def segment_by_threshold(image: np.ndarray, config: dict) -> dict:
    """
    Segmentación directa por rango de color HSV (umbralización).
    Más rápida que K-means pero requiere rangos definidos manualmente.

    Args:
        image: Imagen BGR.
        config: Configuración del proyecto.

    Returns:
        Diccionario con máscara y overlay.
    """
    cfg = config["segmentation"]
    img_hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)

    lower = np.array([cfg["disease_hue_min"],
                      cfg["disease_sat_min"],
                      cfg["disease_val_min"]], dtype=np.uint8)
    upper = np.array([cfg["disease_hue_max"], 255, 255], dtype=np.uint8)

    mask    = cv2.inRange(img_hsv, lower, upper)
    overlay = image.copy()
    overlay[mask > 0] = [0, 0, 220]  # Rojo en BGR

    total   = image.shape[0] * image.shape[1]
    disease = int(np.sum(mask > 0))

    return {
        "mask": mask,
        "overlay": overlay,
        "disease_ratio": round(disease / total * 100, 2),
    }


# ── Visualización ────────────────────────────────────────────────────────────

def plot_segmentation_results(original: np.ndarray,
                               seg_result: dict,
                               metrics: dict,
                               save_path: str = None) -> plt.Figure:
    """
    Visualiza la imagen original, la segmentación por clusters
    y la máscara de la zona enferma.

    Args:
        original: Imagen BGR original.
        seg_result: Resultado de segment_kmeans_hsv().
        metrics: Resultado de compute_cluster_metrics().
        save_path: Ruta para guardar (opcional).

    Returns:
        Objeto Figure de matplotlib.
    """
    disease_idx  = metrics["disease_cluster_idx"]
    disease_mask = seg_result["cluster_masks"][disease_idx]

    fig, axes = plt.subplots(1, 3, figsize=(15, 5))

    # Original
    axes[0].imshow(cv2.cvtColor(original, cv2.COLOR_BGR2RGB))
    axes[0].set_title("Imagen original")
    axes[0].axis("off")

    # Segmentación por cluster
    seg_rgb = cv2.cvtColor(seg_result["segmented_img"], cv2.COLOR_BGR2RGB)
    axes[1].imshow(seg_rgb)
    axes[1].set_title(f"K-means segmentado (k={len(seg_result['centers'])})")
    axes[1].axis("off")

    # Máscara de zona enferma
    axes[2].imshow(disease_mask, cmap="Reds")
    axes[2].set_title(
        f"Zona enferma — cluster {disease_idx}\n"
        f"Área: {metrics['disease_ratio']:.1f}%"
    )
    axes[2].axis("off")

    plt.suptitle("Segmentación K-means sin supervisión (espacio HSV)", fontsize=12)
    plt.tight_layout()

    if save_path:
        Path(save_path).parent.mkdir(parents=True, exist_ok=True)
        plt.savefig(save_path, dpi=150, bbox_inches="tight")
        print(f"[segmentation] Resultado guardado en {save_path}")
    return fig


def plot_cluster_distribution(metrics: dict,
                               save_path: str = None) -> plt.Figure:
    """
    Gráfica de barras con la distribución de píxeles por cluster.

    Args:
        metrics: Resultado de compute_cluster_metrics().
        save_path: Ruta para guardar (opcional).

    Returns:
        Objeto Figure de matplotlib.
    """
    clusters    = metrics["clusters"]
    labels_bar  = [f"Cluster {c['id']}" for c in clusters]
    percentages = [c["percentage"] for c in clusters]
    colors_bar  = [
        "#e74c3c" if c["is_disease"] else "#27ae60"
        for c in clusters
    ]

    fig, ax = plt.subplots(figsize=(7, 4))
    bars = ax.bar(labels_bar, percentages, color=colors_bar, edgecolor="none")
    ax.set_ylabel("% de píxeles")
    ax.set_title("Distribución de píxeles por cluster")
    ax.set_ylim(0, 100)

    for bar, pct in zip(bars, percentages):
        ax.text(bar.get_x() + bar.get_width() / 2,
                bar.get_height() + 1.5,
                f"{pct:.1f}%",
                ha="center", fontsize=10)

    ax.legend(
        handles=[
            plt.Rectangle((0, 0), 1, 1, color="#e74c3c", label="Enfermedad"),
            plt.Rectangle((0, 0), 1, 1, color="#27ae60", label="Sano/fondo"),
        ],
        loc="upper right"
    )
    plt.tight_layout()

    if save_path:
        Path(save_path).parent.mkdir(parents=True, exist_ok=True)
        plt.savefig(save_path, dpi=150, bbox_inches="tight")
        print(f"[segmentation] Distribución guardada en {save_path}")
    return fig


# ── Pipeline de segmentación ─────────────────────────────────────────────────

def run_segmentation(image: np.ndarray, config: dict) -> dict:
    """
    Ejecuta el pipeline completo de segmentación K-means.

    Args:
        image: Imagen BGR preprocesada.
        config: Configuración del proyecto.

    Returns:
        Resultado combinado con segmentación y métricas.
    """
    cfg = config["segmentation"]

    seg = segment_kmeans_hsv(
        image,
        k=cfg["kmeans_k"],
        max_iter=cfg["kmeans_max_iter"],
        attempts=cfg["kmeans_attempts"]
    )

    disease_idx = identify_disease_cluster(seg["centers"])
    metrics     = compute_cluster_metrics(seg["labels"],
                                          seg["centers"],
                                          disease_idx)

    return {**seg, "metrics": metrics}


# ── Ejemplo de uso ──────────────────────────────────────────────────────────
if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("Uso: python segmentation.py <ruta_imagen>")
        sys.exit(1)

    config = load_config()
    img = cv2.imread(sys.argv[1])
    img = cv2.resize(img, tuple(config["preprocessing"]["image_size"]))

    result = run_segmentation(img, config)
    metrics = result["metrics"]

    print(f"\nSegmentación K-means (k={config['segmentation']['kmeans_k']})")
    print(f"Cluster de enfermedad: {metrics['disease_cluster_idx']}")
    print(f"Área enferma estimada: {metrics['disease_ratio']:.2f}%")
    print("\nDetalle por cluster:")
    for c in metrics["clusters"]:
        tag = " ← ENFERMEDAD" if c["is_disease"] else ""
        print(f"  Cluster {c['id']}: {c['percentage']:.1f}% | "
              f"HSV centro: {c['hsv_center']}{tag}")

    plot_segmentation_results(img, result, metrics,
                               save_path="outputs/segmented/kmeans_result.png")
    plot_cluster_distribution(metrics,
                               save_path="outputs/metrics/cluster_dist.png")
    plt.show()
