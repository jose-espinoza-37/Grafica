"""
cnn_model.py
============
Definición, construcción y carga del modelo CNN para clasificación
de hojas (sana / enferma) mediante TRANSFER LEARNING.

Soporta dos backbones preentrenados en ImageNet:
    - MobileNetV2  (ligero, rápido — recomendado para la demo)
    - ResNet18     (un poco más pesado, suele dar algo más de precisión)

Incluye además:
    - Transformaciones de entrada (con/sin data augmentation)
    - Inferencia sobre una imagen (ruta o array BGR de OpenCV)
    - Un Grad-CAM ligero (con hooks) para generar el mapa de
      localización que se usa en la comparativa (IoU contra el método clásico)

Responsable: Henry Huanca
"""

import cv2
import numpy as np
from PIL import Image
from pathlib import Path

import torch
import torch.nn as nn
import torch.nn.functional as F
from torchvision import models, transforms

from utils import load_config, get_device, get_section, count_parameters


# Parámetros por defecto de la CNN (se sobreescriben con config["cnn"] si existe)
DEFAULT_CNN = {
    "backbone":        "mobilenet_v2",   # "mobilenet_v2" | "resnet18"
    "pretrained":      True,             # usar pesos ImageNet
    "freeze_backbone": True,             # congelar el extractor (transfer learning)
    "dropout":         0.3,
    "input_size":      224,              # tamaño de entrada de la CNN
    "class_names":     ["healthy", "diseased"],
    "normalize_mean":  [0.485, 0.456, 0.406],   # stats ImageNet
    "normalize_std":   [0.229, 0.224, 0.225],
}


# ── Construcción del modelo ───────────────────────────────────────────────────

def build_model(backbone: str = "mobilenet_v2",
                num_classes: int = 2,
                pretrained: bool = True,
                freeze_backbone: bool = True,
                dropout: float = 0.3) -> nn.Module:
    """
    Construye un modelo de clasificación a partir de un backbone preentrenado,
    reemplazando la última capa por una cabeza nueva de `num_classes` salidas.

    Args:
        backbone: 'mobilenet_v2' o 'resnet18'.
        num_classes: Número de clases (2 = sana/enferma).
        pretrained: Cargar pesos preentrenados en ImageNet.
        freeze_backbone: Congelar el extractor de características.
        dropout: Probabilidad de dropout en la cabeza.

    Returns:
        Modelo de PyTorch (nn.Module).
    """
    backbone = backbone.lower()

    if backbone == "mobilenet_v2":
        weights = models.MobileNet_V2_Weights.IMAGENET1K_V1 if pretrained else None
        model = models.mobilenet_v2(weights=weights)
        in_features = model.classifier[-1].in_features
        if freeze_backbone:
            for p in model.features.parameters():
                p.requires_grad = False
        model.classifier = nn.Sequential(
            nn.Dropout(dropout),
            nn.Linear(in_features, num_classes),
        )

    elif backbone == "resnet18":
        weights = models.ResNet18_Weights.IMAGENET1K_V1 if pretrained else None
        model = models.resnet18(weights=weights)
        in_features = model.fc.in_features
        if freeze_backbone:
            for name, p in model.named_parameters():
                if not name.startswith("fc"):
                    p.requires_grad = False
        model.fc = nn.Sequential(
            nn.Dropout(dropout),
            nn.Linear(in_features, num_classes),
        )

    else:
        raise ValueError(
            f"Backbone no soportado: '{backbone}'. Usa 'mobilenet_v2' o 'resnet18'."
        )

    return model


def get_target_layer(model: nn.Module, backbone: str) -> nn.Module:
    """
    Devuelve la última capa convolucional del backbone, que es donde
    Grad-CAM engancha los hooks para generar el mapa de activación.
    """
    backbone = backbone.lower()
    if backbone == "mobilenet_v2":
        return model.features[-1]
    if backbone == "resnet18":
        return model.layer4[-1]
    raise ValueError(f"Backbone no soportado para Grad-CAM: {backbone}")


# ── Transformaciones ──────────────────────────────────────────────────────────

def get_transforms(input_size: int = 224,
                   mean=None,
                   std=None,
                   train: bool = False) -> transforms.Compose:
    """
    Devuelve el pipeline de transformaciones de torchvision.

    En entrenamiento aplica DATA AUGMENTATION (recortes, giros, rotación,
    variación de color) para que el modelo generalice mejor.
    En validación/test solo redimensiona y normaliza.
    """
    mean = mean or DEFAULT_CNN["normalize_mean"]
    std  = std  or DEFAULT_CNN["normalize_std"]

    if train:
        return transforms.Compose([
            transforms.RandomResizedCrop(input_size, scale=(0.7, 1.0)),
            transforms.RandomHorizontalFlip(),
            transforms.RandomVerticalFlip(),
            transforms.RandomRotation(20),
            transforms.ColorJitter(brightness=0.2, contrast=0.2,
                                   saturation=0.2, hue=0.05),
            transforms.ToTensor(),
            transforms.Normalize(mean, std),
        ])

    return transforms.Compose([
        transforms.Resize((input_size, input_size)),
        transforms.ToTensor(),
        transforms.Normalize(mean, std),
    ])


def _to_pil(image) -> Image.Image:
    """
    Convierte la entrada a una imagen PIL en RGB.
    Acepta: ruta (str/Path), array BGR de OpenCV o imagen PIL.
    """
    if isinstance(image, (str, Path)):
        bgr = cv2.imread(str(image))
        if bgr is None:
            raise ValueError(f"No se pudo leer la imagen: {image}")
        rgb = cv2.cvtColor(bgr, cv2.COLOR_BGR2RGB)
        return Image.fromarray(rgb)
    if isinstance(image, np.ndarray):
        # Se asume BGR (formato de OpenCV)
        rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        return Image.fromarray(rgb)
    if isinstance(image, Image.Image):
        return image.convert("RGB")
    raise TypeError(f"Tipo de imagen no soportado: {type(image)}")


# ── Carga del modelo entrenado ────────────────────────────────────────────────

def load_model(weights_path: str,
               config: dict = None,
               device: torch.device = None) -> tuple:
    """
    Carga un modelo entrenado desde un checkpoint.

    Soporta dos formatos de archivo:
        1. Checkpoint dict (recomendado, generado por train.py) que incluye
           backbone, class_names, input_size y normalización.
        2. state_dict "pelado" (solo pesos) — usa la config para reconstruir.

    Returns:
        (model, meta) donde meta tiene backbone, class_names, input_size, etc.
    """
    device = device or get_device()
    config = config or {}
    ccfg = get_section(config, "cnn", DEFAULT_CNN)

    ckpt = torch.load(weights_path, map_location=device)

    if isinstance(ckpt, dict) and "model_state" in ckpt:
        backbone     = ckpt.get("backbone", ccfg["backbone"])
        class_names  = ckpt.get("class_names", ccfg["class_names"])
        input_size   = ckpt.get("input_size", ccfg["input_size"])
        mean         = ckpt.get("normalize_mean", ccfg["normalize_mean"])
        std          = ckpt.get("normalize_std", ccfg["normalize_std"])
        state        = ckpt["model_state"]
    else:
        backbone     = ccfg["backbone"]
        class_names  = ccfg["class_names"]
        input_size   = ccfg["input_size"]
        mean         = ccfg["normalize_mean"]
        std          = ccfg["normalize_std"]
        state        = ckpt

    model = build_model(backbone, num_classes=len(class_names),
                        pretrained=False, freeze_backbone=False)
    model.load_state_dict(state)
    model.to(device).eval()

    meta = {
        "backbone":       backbone,
        "class_names":    class_names,
        "input_size":     input_size,
        "normalize_mean": mean,
        "normalize_std":  std,
        "device":         str(device),
    }
    return model, meta


# ── Inferencia ────────────────────────────────────────────────────────────────

@torch.no_grad()
def predict_image(model: nn.Module,
                  image,
                  meta: dict = None,
                  transform=None,
                  device: torch.device = None) -> dict:
    """
    Clasifica una sola imagen.

    Args:
        model: Modelo cargado (en modo eval).
        image: ruta, array BGR o imagen PIL.
        meta: metadatos devueltos por load_model (class_names, input_size, ...).
        transform: transformación a aplicar (si None, se construye desde meta).

    Returns:
        Diccionario con:
            'label_idx'     - índice de la clase predicha
            'label'         - nombre de la clase predicha
            'confidence'    - probabilidad de la clase predicha
            'probabilities' - probabilidades de todas las clases
    """
    device = device or get_device()
    meta = meta or {}
    class_names = meta.get("class_names", DEFAULT_CNN["class_names"])
    input_size  = meta.get("input_size", DEFAULT_CNN["input_size"])
    mean        = meta.get("normalize_mean", DEFAULT_CNN["normalize_mean"])
    std         = meta.get("normalize_std", DEFAULT_CNN["normalize_std"])

    if transform is None:
        transform = get_transforms(input_size, mean, std, train=False)

    pil = _to_pil(image)
    x   = transform(pil).unsqueeze(0).to(device)

    logits = model(x)
    probs  = F.softmax(logits, dim=1).cpu().numpy()[0]
    idx    = int(np.argmax(probs))

    return {
        "label_idx":     idx,
        "label":         class_names[idx] if idx < len(class_names) else str(idx),
        "confidence":    float(probs[idx]),
        "probabilities": probs.tolist(),
    }


# ── Grad-CAM (mapa de localización) ───────────────────────────────────────────

class GradCAM:
    """
    Implementación ligera de Grad-CAM mediante hooks de forward/backward.
    Genera un mapa de calor que indica en qué regiones se "fijó" la CNN
    para tomar su decisión. Ese mapa se usa luego (umbralizado) como
    máscara para comparar contra el método clásico mediante IoU.
    """

    def __init__(self, model: nn.Module, target_layer: nn.Module):
        self.model = model
        self.target_layer = target_layer
        self.activations = None
        self.gradients = None
        self._fwd = target_layer.register_forward_hook(self._save_activation)
        self._bwd = target_layer.register_full_backward_hook(self._save_gradient)

    def _save_activation(self, module, inp, out):
        self.activations = out.detach()

    def _save_gradient(self, module, grad_in, grad_out):
        self.gradients = grad_out[0].detach()

    def __call__(self, x: torch.Tensor, class_idx: int = None) -> np.ndarray:
        """
        Args:
            x: tensor de entrada (1, C, H, W).
            class_idx: clase objetivo (si None, usa la predicha).

        Returns:
            Mapa Grad-CAM normalizado [0, 1] del tamaño de la entrada (H x W).
        """
        self.model.zero_grad()
        logits = self.model(x)
        if class_idx is None:
            class_idx = int(logits.argmax(dim=1).item())
        score = logits[:, class_idx].sum()
        score.backward()

        # Peso por canal = promedio espacial del gradiente
        weights = self.gradients.mean(dim=(2, 3), keepdim=True)
        cam = F.relu((weights * self.activations).sum(dim=1, keepdim=True))
        cam = F.interpolate(cam, size=x.shape[2:], mode="bilinear",
                            align_corners=False)
        cam = cam.squeeze().cpu().numpy()

        cam -= cam.min()
        if cam.max() > 0:
            cam /= cam.max()
        return cam

    def remove(self):
        """Elimina los hooks (llamar al terminar para liberar memoria)."""
        self._fwd.remove()
        self._bwd.remove()


def get_cnn_disease_mask(model: nn.Module,
                         image,
                         meta: dict = None,
                         out_size: tuple = (256, 256),
                         threshold: float = 0.5,
                         device: torch.device = None) -> np.ndarray:
    """
    Genera una máscara binaria de la zona "enferma" según la CNN,
    umbralizando el mapa Grad-CAM. Sirve para calcular el IoU contra
    la máscara del método clásico.

    Returns:
        Máscara uint8 (0 o 255) del tamaño `out_size`.
    """
    device = device or get_device()
    meta = meta or {}
    backbone   = meta.get("backbone", DEFAULT_CNN["backbone"])
    input_size = meta.get("input_size", DEFAULT_CNN["input_size"])
    mean       = meta.get("normalize_mean", DEFAULT_CNN["normalize_mean"])
    std        = meta.get("normalize_std", DEFAULT_CNN["normalize_std"])
    class_names = meta.get("class_names", DEFAULT_CNN["class_names"])

    transform = get_transforms(input_size, mean, std, train=False)
    x = transform(_to_pil(image)).unsqueeze(0).to(device)

    # Clase "diseased" si existe; si no, la predicha
    disease_idx = class_names.index("diseased") if "diseased" in class_names else None

    cam_engine = GradCAM(model, get_target_layer(model, backbone))
    try:
        cam = cam_engine(x, class_idx=disease_idx)
    finally:
        cam_engine.remove()

    cam = cv2.resize(cam, out_size, interpolation=cv2.INTER_LINEAR)
    mask = (cam >= threshold).astype(np.uint8) * 255
    return mask


# ── Ejemplo de uso ──────────────────────────────────────────────────────────
if __name__ == "__main__":
    config = load_config()
    ccfg = get_section(config, "cnn", DEFAULT_CNN)

    model = build_model(
        backbone=ccfg["backbone"],
        num_classes=len(ccfg["class_names"]),
        pretrained=ccfg["pretrained"],
        freeze_backbone=ccfg["freeze_backbone"],
        dropout=ccfg["dropout"],
    )

    total, trainable = count_parameters(model)
    print(f"Backbone: {ccfg['backbone']}")
    print(f"Parámetros totales:    {total:,}")
    print(f"Parámetros entrenables:{trainable:,}")
    print(f"Clases: {ccfg['class_names']}")

    # Prueba de forward con un tensor aleatorio
    dummy = torch.randn(1, 3, ccfg["input_size"], ccfg["input_size"])
    out = model(dummy)
    print(f"Salida del modelo: {out.shape}  (logits por clase)")