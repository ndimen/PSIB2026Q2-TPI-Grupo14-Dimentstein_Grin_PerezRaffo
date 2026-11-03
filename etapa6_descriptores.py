# etapa6_descriptores.py - Etapa 6: descriptores morfológicos y de intensidad del tumor
# Uso (desde la raíz del repo):  python etapa6_descriptores.py
from pathlib import Path

import matplotlib
matplotlib.use("Agg")  # backend sin ventanas: solo guardamos archivos
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scipy.stats import entropy, kurtosis, skew
from skimage.measure import regionprops

from etapa0_datos import load_flair, load_mask, build_index
from etapa4_segmentacion import simple_features, segment, postprocess  # TODO: usar compute_features de etapa2

SEED = 42
N_SLICES = 200   # cortes con tumor a analizar (None = todos; cada corte tarda ~1 s por el preprocesamiento)
N_BINS = 32      # bins del histograma para la entropía de intensidad

DESCRIPTORS = ["area", "perimetro", "excentricidad", "solidez", "eje_mayor", "eje_menor",
               "media", "desvio", "asimetria", "curtosis", "entropia"]


def compute_descriptors(img, mask):
    """Dict con descriptores de forma (regionprops) y de intensidad de img dentro de mask."""
    if not mask.any():                                   # máscara vacía: no hay región que describir
        return dict.fromkeys(DESCRIPTORS, np.nan)
    # Toda la máscara como UNA sola región (label 1), aunque tenga varias componentes
    r = regionprops(mask.astype(np.uint8))[0]
    vals = img[mask.astype(bool)]                        # intensidades del tumor
    hist, _ = np.histogram(vals, bins=N_BINS)            # distribución de intensidades para la entropía
    return {
        "area": r.area,                                  # píxeles del tumor
        "perimetro": r.perimeter,                        # longitud del borde (irregularidad junto con el área)
        "excentricidad": r.eccentricity,                 # 0 = círculo, cerca de 1 = alargado
        "solidez": r.solidity,                           # área / área de la envolvente convexa (1 = convexo)
        "eje_mayor": r.axis_major_length,                # ejes de la elipse con los mismos momentos
        "eje_menor": r.axis_minor_length,
        "media": vals.mean(),                            # hiperintensidad media
        "desvio": vals.std(),                            # heterogeneidad
        "asimetria": skew(vals),                         # cola hacia valores altos (>0) o bajos (<0)
        "curtosis": kurtosis(vals),                      # colas pesadas respecto de una gaussiana (exceso)
        "entropia": entropy(hist, base=2),               # desorden del histograma en bits
    }


if __name__ == "__main__":
    out = Path("results")
    out.mkdir(exist_ok=True)
    idx = build_index()
    con_tumor = idx[idx["has_tumor"]]
    if N_SLICES is not None:                             # muestra fija y reproducible
        con_tumor = con_tumor.sample(min(N_SLICES, len(con_tumor)), random_state=SEED)

    rows = []
    for _, f in con_tumor.iterrows():
        feats = simple_features(load_flair(f["img_path"]))
        pre = feats[..., 0]                              # intensidad z-score: comparable entre pacientes
        pred = postprocess(segment(feats))
        gt = load_mask(f["mask_path"]).astype(bool)
        d_gt, d_pred = compute_descriptors(pre, gt), compute_descriptors(pre, pred)
        # Una fila por corte, con sufijos _gt y _pred para cada descriptor
        rows.append({"patient": f["patient"], "slice": f["slice"],
                     **{f"{k}_gt": v for k, v in d_gt.items()},
                     **{f"{k}_pred": v for k, v in d_pred.items()}})
    df = pd.DataFrame(rows)
    df.round(4).to_csv(out / "etapa6_descriptores.csv", index=False)

    # Concordancia GT vs predicha por descriptor: Pearson (lineal) y Spearman (orden, robusta a outliers)
    corr = pd.DataFrame({
        "pearson": [df[f"{d}_gt"].corr(df[f"{d}_pred"]) for d in DESCRIPTORS],
        "spearman": [df[f"{d}_gt"].corr(df[f"{d}_pred"], method="spearman") for d in DESCRIPTORS],
    }, index=DESCRIPTORS).round(3)
    corr.to_csv(out / "etapa6_correlacion.csv")

    # Dispersión GT vs predicha con la recta identidad (puntos sobre la recta = descriptor bien recuperado)
    fig, ax = plt.subplots(3, 4, figsize=(16, 11))
    for a, d in zip(ax.ravel(), DESCRIPTORS):
        x, y = df[f"{d}_gt"], df[f"{d}_pred"]
        a.scatter(x, y, s=8, alpha=0.5)
        lim = [np.nanmin([x.min(), y.min()]), np.nanmax([x.max(), y.max()])]
        a.plot(lim, lim, "k--", lw=1)
        a.set_title(f"{d} | r = {corr.loc[d, 'pearson']:.2f}", fontsize=10)
        a.set_xlabel("GT")
        a.set_ylabel("Predicha")
    ax.ravel()[-1].axis("off")                           # 11 descriptores en una grilla de 12
    plt.tight_layout()
    plt.savefig(out / "etapa6_gt_vs_pred.png", dpi=150)
    plt.close()

    print(f"Cortes analizados: {len(df)} | Predicciones vacías: {df['area_pred'].isna().sum()}")
    print(corr.to_string())
    print(f"Resultados guardados en {out}/")
