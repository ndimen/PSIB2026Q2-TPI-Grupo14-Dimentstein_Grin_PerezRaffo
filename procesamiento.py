# etapa1_preprocesamiento.py
# Etapa 1: preprocesamiento de FLAIR (máscara de cerebro, denoising, normalización) + análisis de compresión.
import os
import glob
import cv2
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")  # backend sin ventana: solo guardamos figuras
import matplotlib.pyplot as plt
from scipy import ndimage as ndi
from skimage.filters import threshold_otsu
from skimage.restoration import denoise_nl_means, estimate_sigma
from skimage.metrics import peak_signal_noise_ratio as psnr, structural_similarity as ssim

from cargadatos import load_flair  # TODO: renombrar a etapa0_datos cuando Nico unifique el nombre

BEST_METHOD = "nlm"   # filtro elegido para preprocess(); se confirma con la tabla del main
MASK_FACTOR = 0.3     # fracción del umbral de Otsu usada para separar cerebro de fondo (ajustable)


def brain_mask(img):
    """Devuelve la máscara booleana del cerebro (umbral de Otsu, mayor componente conexa, sin huecos)."""
    m = img > threshold_otsu(img) * MASK_FACTOR   # umbral bajo: incluye tejido oscuro pero excluye el fondo
    m = ndi.binary_opening(m, iterations=2)       # la apertura saca puntos sueltos y bordes ruidosos
    m = ndi.binary_fill_holes(m)                  # rellena huecos internos (LCR anulado, ventrículos)
    lab, n = ndi.label(m)                         # componentes conexas
    if n == 0:                                    # imagen vacía: devolvemos la máscara tal cual
        return m
    return lab == (np.argmax(np.bincount(lab.ravel())[1:]) + 1)  # nos quedamos con la más grande


def normalize(img, mask):
    """Z-score usando solo los píxeles dentro del cerebro; el fondo queda en 0."""
    out = np.zeros_like(img, dtype=np.float64)
    vals = img[mask]                                              # solo píxeles de cerebro
    out[mask] = (vals - vals.mean()) / (vals.std() + 1e-8)        # (x - media) / desvío; 1e-8 evita división por 0
    return out


# Cada filtro trabaja sobre una imagen float32 escalada a [0, 1]
FILTERS = {
    "median": lambda x: ndi.median_filter(x, size=3),            # mediana 3x3: bueno contra ruido impulsivo
    "gaussian": lambda x: ndi.gaussian_filter(x, sigma=1),       # suavizado lineal: desenfoca bordes
    "bilateral": lambda x: cv2.bilateralFilter(x, 5, 0.1, 2),    # d=5, sigmaColor=0.1 (en [0,1]), sigmaSpace=2: preserva bordes
    "nlm": lambda x: denoise_nl_means(                           # non-local means: promedia parches similares
        x, patch_size=5, patch_distance=6,
        h=0.8 * estimate_sigma(x), sigma=estimate_sigma(x), fast_mode=True),
}


def denoise(img, method=BEST_METHOD):
    """Aplica el filtro 'method' (median, gaussian, bilateral, nlm) conservando el rango original."""
    if method not in FILTERS:
        raise ValueError(f"method debe ser uno de {list(FILTERS)}")
    lo, rng = img.min(), (np.ptp(img) or 1.0)           # rango original (evita dividir por 0)
    x = ((img - lo) / rng).astype(np.float32)           # escalamos a [0, 1] para que los parámetros sean comparables
    return FILTERS[method](x) * rng + lo                # filtramos y volvemos al rango original


def preprocess(img):
    """Pipeline: máscara de cerebro -> denoising -> zero fuera del cerebro -> z-score dentro del cerebro."""
    mask = brain_mask(img)                    # la máscara se calcula sobre la imagen original
    den = denoise(img, BEST_METHOD) * mask    # el filtro puede "chorrear" fuera del borde: lo anulamos
    return normalize(den, mask)


def jpeg_roundtrip(img_u8, quality):
    """Comprime a JPEG con la calidad dada y devuelve (imagen reconstruida, tamaño en bytes)."""
    ok, buf = cv2.imencode(".jpg", img_u8, [cv2.IMWRITE_JPEG_QUALITY, quality])  # codifica en memoria
    return cv2.imdecode(buf, cv2.IMREAD_GRAYSCALE), len(buf)


if __name__ == "__main__":
    os.makedirs("results", exist_ok=True)
    rng = np.random.default_rng(42)  # semilla fija

    # --- Elegimos un corte central del primer paciente (descubriendo carpetas, sin armar nombres a mano) ---
    patient = sorted(glob.glob("data/TCGA_*"))[0]
    slices = [f for f in glob.glob(os.path.join(patient, "*.tif")) if not f.endswith("_mask.tif")]
    slices.sort(key=lambda f: int(os.path.splitext(f)[0].split("_")[-1]))  # orden numérico del corte (_7 antes que _10)
    img = load_flair(slices[len(slices) // 2])
    print("Corte usado:", slices[len(slices) // 2])

    # --- 0) Chequeo de la máscara: valores del fondo vs cerebro para validar el umbral ---
    mask = brain_mask(img)
    print(f"Rango imagen: min={img.min():.2f}, max={img.max():.2f}, umbral usado={threshold_otsu(img) * MASK_FACTOR:.2f}")
    print(f"Fondo: media={img[~mask].mean():.2f} | Cerebro: media={img[mask].mean():.2f} | "
          f"Cerebro ocupa {100 * mask.mean():.1f}% de la imagen")

    # --- 1) Comparación de filtros sobre ruido gaussiano sintético ---
    clean = (img / img.max()).astype(np.float32)                               # referencia limpia en [0, 1]
    noisy = clean + rng.normal(0, 0.05, clean.shape).astype(np.float32)        # ruido gaussiano sigma=0.05
    outs = {"original": clean, "ruidosa": noisy}
    outs.update({m: denoise(noisy, m) for m in FILTERS})                       # una salida por filtro
    rows = [{"imagen": k, "PSNR": psnr(clean, v, data_range=1), "SSIM": ssim(clean, v, data_range=1)}
            for k, v in outs.items() if k != "original"]
    df = pd.DataFrame(rows).round(4)
    df.to_csv("results/etapa1_filtros.csv", index=False)
    print(df.to_string(index=False))
    print("Mejor filtro por SSIM:", df[df.imagen.isin(FILTERS)].sort_values("SSIM").iloc[-1].imagen)

    fig, axs = plt.subplots(2, 3, figsize=(12, 8))
    for ax, (k, v) in zip(axs.ravel(), outs.items()):
        ax.imshow(v, cmap="gray", vmin=0, vmax=1)
        ttl = k if k == "original" else f"{k}\nPSNR {psnr(clean, v, data_range=1):.2f} dB | SSIM {ssim(clean, v, data_range=1):.3f}"
        ax.set_title(ttl)
        ax.axis("off")
    plt.tight_layout()
    plt.savefig("results/etapa1_filtros.png", dpi=150)
    plt.close()

    # --- 2) Compresión JPEG con calidades 90, 50 y 10 ---
    ref = np.round(clean * 255).astype(np.uint8)                               # imagen de referencia de 8 bits
    comp = []
    for q in (90, 50, 10):
        rec, nbytes = jpeg_roundtrip(ref, q)
        comp.append({"calidad": q, "PSNR": psnr(ref, rec, data_range=255),
                     "SSIM": ssim(ref, rec, data_range=255), "bytes": nbytes})
    dfc = pd.DataFrame(comp).round(4)
    dfc.to_csv("results/etapa1_compresion.csv", index=False)
    print(f"Tamaño sin comprimir: {ref.nbytes} bytes")
    print(dfc.to_string(index=False))

    fig, (a1, a2) = plt.subplots(1, 2, figsize=(11, 4))
    a1.plot(dfc.calidad, dfc.PSNR, "o-b")                                      # PSNR (dB) vs calidad
    a1.set_xlabel("Calidad JPEG"); a1.set_ylabel("PSNR (dB)", color="b")
    a1b = a1.twinx()
    a1b.plot(dfc.calidad, dfc.SSIM, "s--r")                                    # SSIM vs calidad en eje derecho
    a1b.set_ylabel("SSIM", color="r")
    a1.set_title("Calidad de reconstrucción")
    a2.bar(dfc.calidad.astype(str), dfc.bytes)                                 # tamaño en bytes por calidad
    a2.set_xlabel("Calidad JPEG"); a2.set_ylabel("Tamaño (bytes)")
    a2.set_title("Tamaño del archivo")
    plt.tight_layout()
    plt.savefig("results/etapa1_compresion.png", dpi=150)
    plt.close()

    # --- 3) Demo de preprocess(): original, máscara y resultado ---
    pre = preprocess(img)
    fig, axs = plt.subplots(1, 3, figsize=(12, 4))
    for ax, im, t in zip(axs, (img, mask, pre), ("FLAIR original", "Máscara de cerebro", "Preprocesada (z-score)")):
        ax.imshow(im, cmap="gray"); ax.set_title(t); ax.axis("off")
    plt.tight_layout()
    plt.savefig("results/etapa1_preprocess.png", dpi=150)
    plt.close()
    print(f"Z-score dentro del cerebro: media={pre[mask].mean():.3f}, desvío={pre[mask].std():.3f}")