# Librerías estándar para manejar rutas, tiempos y búsqueda de archivos
import os
import time
from glob import glob

# OpenCV se usa solo para reescalar el mapa de wavelet al tamaño original
import cv2
import matplotlib
matplotlib.use("Agg")  # backend sin ventana: solo guardamos figuras, nunca plt.show
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import pywt  # PyWavelets: transformada wavelet
# Filtros espaciales de scipy: suavizado, Laplaciano y filtro uniforme (media móvil)
from scipy.ndimage import gaussian_filter, laplace, uniform_filter
# Herramientas de scikit-image: conversión a uint8, LBP, Gabor, entropía local, Sobel y elemento estructurante
from skimage import img_as_ubyte
from skimage.feature import local_binary_pattern
from skimage.filters import gabor, rank, sobel
from skimage.morphology import disk

# Etapas de Nico: carga de datos y preprocesamiento
from etapa0_datos import load_flair, load_mask
from etapa1_preprocesamiento import preprocess

# Semilla fija para que todo sea reproducible
SEED = 42
np.random.seed(SEED)

# Nombres de los mapas, en el mismo orden en que se apilan en compute_features
FEATURE_NAMES = [
    "intensidad", "media_local", "desvio_local", "entropia_local",
    "sobel", "laplaciano", "lbp",
    "gabor_0", "gabor_45", "gabor_90",
    "wavelet_detalle", "asimetria",
]

WIN = 9  # tamaño de la ventana para media y desvío locales (px)


def to_unit(img):
    """Reescala a [0,1] recortando percentiles 1 y 99 (robusto a outliers)."""
    lo, hi = np.percentile(img, [1, 99])  # límites robustos, ignoran píxeles extremos
    return np.clip((img - lo) / (hi - lo + 1e-8), 0, 1)  # normaliza y recorta a [0,1]


def local_mean_std(x, size=WIN):
    """Media y desvío locales con filtro uniforme: std = sqrt(E[x^2] - E[x]^2)."""
    mean = uniform_filter(x, size)  # media en cada ventana size x size
    var = uniform_filter(x * x, size) - mean ** 2  # varianza = E[x^2] - E[x]^2
    return mean, np.sqrt(np.clip(var, 0, None))  # clip evita negativos por redondeo numérico


def wavelet_detail(x):
    """Magnitud de los detalles de una DWT Haar nivel 1, reescalada al tamaño original."""
    _, (ch, cv, cd) = pywt.dwt2(x, "haar")  # detalles horizontal, vertical y diagonal (mitad de tamaño)
    mag = np.sqrt(ch ** 2 + cv ** 2 + cd ** 2)  # magnitud combinada de los 3 detalles
    # Volvemos al tamaño original (cv2.resize recibe (ancho, alto))
    return cv2.resize(mag, (x.shape[1], x.shape[0]), interpolation=cv2.INTER_LINEAR)


def hemispheric_asymmetry(x):
    """|imagen - imagen reflejada| respecto del eje medio (centroide horizontal de intensidad)."""
    w = x.shape[1]  # cantidad de columnas
    # Centroide de columnas ponderado por intensidad = estimación del eje medio del cerebro
    c = (x.sum(axis=0) * np.arange(w)).sum() / (x.sum() + 1e-8)
    flipped = x[:, ::-1]  # espejo respecto del centro de la imagen (el eje queda en w-1-c)
    # Desplazamos el espejo para que el eje reflejado coincida con el eje real c
    # (np.roll cierra por el borde: genera un pequeño artefacto en los costados, aceptable aquí)
    flipped = np.roll(flipped, int(round(2 * c - w + 1)), axis=1)
    # Valor absoluto: un tumor en cualquier hemisferio debe dar asimetría alta; suavizamos el ruido
    return gaussian_filter(np.abs(x - flipped), 2)


def compute_features(img):
    """Devuelve un array (H, W, n_features) con los mapas de FEATURE_NAMES (img: 2D ya preprocesada)."""
    x = to_unit(img.astype(np.float64))  # intensidad normalizada [0,1]
    x8 = img_as_ubyte(x)  # versión uint8, requerida por entropy y LBP

    mean, std = local_mean_std(x)  # estadísticos locales
    entropy = rank.entropy(x8, disk(5))  # entropía local (disco de radio 5)
    grad = sobel(x)  # magnitud del gradiente
    lap = laplace(gaussian_filter(x, 1))  # Laplaciano sobre imagen suavizada (menos ruido)
    lbp = local_binary_pattern(x8, P=8, R=1, method="uniform")  # textura LBP (valores 0..9)

    # 3 Gabor a frecuencia fija y 3 orientaciones; usamos la magnitud (real + imaginaria)
    gabors = [np.hypot(*gabor(x, frequency=0.2, theta=t)) for t in (0, np.pi / 4, np.pi / 2)]

    # Apilamos todos los mapas en el mismo orden que FEATURE_NAMES
    maps = [x, mean, std, entropy, grad, lap, lbp, *gabors,
            wavelet_detail(x), hemispheric_asymmetry(x)]
    return np.stack(maps, axis=-1).astype(np.float32)  # float32 para ahorrar memoria


def find_tumor_slice(min_pixels=500):
    """Busca (con semilla fija) un corte con tumor grande listando data/ sin armar nombres a mano."""
    masks = sorted(glob(os.path.join("data", "*", "*_mask.tif")))  # todas las máscaras de todos los pacientes
    # Recorremos los cortes en orden aleatorio reproducible hasta encontrar uno con tumor suficiente
    for i in np.random.default_rng(SEED).permutation(len(masks)):
        if load_mask(masks[i]).sum() >= min_pixels:
            return masks[i].replace("_mask.tif", ".tif"), masks[i]  # (ruta imagen, ruta máscara)
    raise RuntimeError("No se encontró ningún corte con tumor en data/")


if __name__ == "__main__":
    os.makedirs("results", exist_ok=True)  # carpeta de salida

    # 1) Elegimos un corte con tumor y lo preprocesamos
    img_path, mask_path = find_tumor_slice()
    mask = load_mask(mask_path) > 0  # máscara booleana
    img = preprocess(load_flair(img_path))  # FLAIR preprocesado
    print("Corte:", os.path.basename(img_path), "| tumor (px):", int(mask.sum()))

    # 2) Calculamos los mapas y medimos el tiempo
    t0 = time.time()
    feats = compute_features(img)
    print(f"Features: {feats.shape} en {time.time() - t0:.2f} s")

    # 3) Figura: FLAIR + máscara + los 12 mapas (grilla 3x5)
    fig, axs = plt.subplots(3, 5, figsize=(18, 11))
    panels = [("FLAIR preprocesado", img), ("Máscara (GT)", mask)] + \
             [(n, feats[..., k]) for k, n in enumerate(FEATURE_NAMES)]
    for ax, (title, m) in zip(axs.ravel(), panels):
        # Gris para la imagen y la máscara, viridis para los mapas de características
        ax.imshow(m, cmap="gray" if title in ("FLAIR preprocesado", "Máscara (GT)") else "viridis")
        ax.contour(mask, levels=[0.5], colors="r", linewidths=0.6)  # contorno del tumor sobre cada mapa
        ax.set_title(title, fontsize=10)
    for ax in axs.ravel():
        ax.axis("off")  # sin ejes, solo imágenes
    fig.tight_layout()
    fig.savefig("results/etapa2_mapas.png", dpi=120)
    plt.close(fig)

    # 4) Tabla: media de cada mapa dentro y fuera del tumor (vectorizado con máscara booleana)
    inside, outside = feats[mask].mean(axis=0), feats[~mask].mean(axis=0)
    pd.DataFrame({"feature": FEATURE_NAMES, "media_tumor": inside, "media_resto": outside,
                  "diferencia": inside - outside}).to_csv("results/etapa2_resumen.csv", index=False)
    print("Guardado: results/etapa2_mapas.png y results/etapa2_resumen.csv")