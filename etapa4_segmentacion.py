# etapa4_segmentacion.py - Etapa 4: segmentar el tumor (línea base con Otsu y método propuesto con k-means)
# Uso (desde la raíz del repo):  python etapa4_segmentacion.py
from pathlib import Path

import matplotlib
matplotlib.use("Agg")  # backend sin ventanas: solo guardamos archivos
import matplotlib.pyplot as plt
import numpy as np
from scipy import ndimage as ndi
from skimage.filters import threshold_otsu
from skimage.morphology import disk
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler

from cargadatos import load_flair, load_mask, build_index  # TODO: renombrar a etapa0_datos cuando se unifique
from procesamiento import brain_mask, preprocess          # TODO: renombrar a etapa1_preprocesamiento

SEED = 42          # semilla fija para k-means
N_CLUSTERS = 3     # 3 grupos: tejido oscuro, parénquima normal e hiperintenso (tumor/edema)
INTENSITY_IDX = 0  # índice de la feature de intensidad dentro del array de features


def simple_features(img):
    """Features provisorias (H, W, 3): intensidad preprocesada, desvío local y gradiente Sobel."""
    # TODO: reemplazar por compute_features de etapa2_mapas y SELECTED_FEATURES de etapa3_seleccion
    pre = preprocess(img)                                          # z-score dentro del cerebro, fondo en 0
    mean = ndi.uniform_filter(pre, size=7)                         # media local en ventana 7x7
    std = np.sqrt(np.clip(ndi.uniform_filter(pre**2, 7) - mean**2, 0, None))  # desvío local: sqrt(E[x²] - E[x]²)
    grad = np.hypot(ndi.sobel(pre, axis=0), ndi.sobel(pre, axis=1))  # módulo del gradiente (bordes)
    return np.stack([pre, std, grad], axis=-1)


def segment_baseline(img):
    """Línea base: umbral de Otsu calculado solo con los píxeles del cerebro."""
    brain = brain_mask(img)                     # sin esto, Otsu separaría cerebro de fondo y no tumor de tejido
    return (img > threshold_otsu(img[brain])) & brain


def segment(features, brain=None, n_clusters=N_CLUSTERS):
    """K-means sobre las features dentro del cerebro; el tumor es el cluster de mayor intensidad media."""
    if brain is None:
        # preprocess deja el fondo exactamente en 0, así que el cerebro es donde la intensidad no es 0
        brain = features[..., INTENSITY_IDX] != 0
    X = StandardScaler().fit_transform(features[brain])     # (n_píxeles, n_features) con cada feature en la misma escala
    labels = KMeans(n_clusters, n_init=10, random_state=SEED).fit_predict(X)
    # Media de la intensidad por cluster sin loops: suma por cluster / cantidad por cluster
    means = np.bincount(labels, weights=X[:, INTENSITY_IDX]) / np.bincount(labels)
    mask = np.zeros(brain.shape, dtype=bool)
    mask[brain] = labels == np.argmax(means)                 # volvemos a la grilla 2D solo con el cluster tumor
    return mask


def postprocess(mask, radius=2):
    """Apertura, cierre, relleno de huecos y componente conexa más grande."""
    se = disk(radius)                                  # elemento estructurante circular
    m = ndi.binary_opening(mask, structure=se)         # saca píxeles sueltos y puentes finos
    m = ndi.binary_closing(m, structure=se)            # cierra grietas pequeñas en el borde del tumor
    m = ndi.binary_fill_holes(m)                       # rellena huecos internos (necrosis, ruido)
    lab, n = ndi.label(m)                              # etiquetamos componentes conexas
    if n == 0:                                         # nada segmentado: devolvemos la máscara vacía
        return m
    return lab == np.argmax(np.bincount(lab.ravel())[1:]) + 1  # nos quedamos con la más grande


if __name__ == "__main__":
    out = Path("results")
    out.mkdir(exist_ok=True)
    idx = build_index()

    # Corte de demo: el de área de tumor mediana (ni el más fácil ni el más difícil)
    con_tumor = idx[idx["has_tumor"]].sort_values("tumor_area")
    fila = con_tumor.iloc[len(con_tumor) // 2]
    img, gt = load_flair(fila["img_path"]), load_mask(fila["mask_path"]).astype(bool)

    # Aplicamos el mismo posprocesamiento a ambos para que la diferencia venga solo de las features
    base = postprocess(segment_baseline(img))
    prop = postprocess(segment(simple_features(img)))

    # Dice rápido solo para el título; la métrica oficial es evaluate() de la etapa 5
    dice = lambda p: 2 * (p & gt).sum() / (p.sum() + gt.sum() + 1e-8)

    fig, ax = plt.subplots(1, 4, figsize=(16, 4))
    paneles = [(None, "FLAIR"), (gt, "Ground truth"),
               (base, f"Línea base (Otsu) | Dice {dice(base):.2f}"),
               (prop, f"Propuesto (k-means) | Dice {dice(prop):.2f}")]
    for a, (m, titulo) in zip(ax, paneles):
        a.imshow(img, cmap="gray")
        if m is not None:
            a.contour(m, levels=[0.5], colors="r")   # borde de la máscara en rojo
        a.set_title(titulo, fontsize=10)
        a.axis("off")
    fig.suptitle(f"{fila['patient']} corte {fila['slice']}")
    plt.savefig(out / "etapa4_segmentacion.png", dpi=150, bbox_inches="tight")
    plt.close()
    print(f"{fila['patient']} corte {fila['slice']} | Dice base: {dice(base):.3f} | Dice propuesto: {dice(prop):.3f}")
    print(f"Figura guardada en {out / 'etapa4_segmentacion.png'}")
