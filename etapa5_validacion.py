# etapa5_validacion.py
# Validación: métricas, línea base (Otsu) vs método propuesto (k-means), ablation por familia
# y promedio opcional por variables clínicas. Sin split train/test (análisis exploratorio).
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from etapa0_datos import build_index, load_flair, load_mask, DATA_DIR
from etapa1_preprocesamiento import brain_mask, preprocess
from etapa2_mapas import compute_features, FEATURE_NAMES
from etapa3_seleccion import SELECTED_FEATURES
from etapa4_segmentacion import segment_baseline, segment, postprocess

SEED = 42
METRICAS = ["Dice", "IoU", "sensibilidad", "especificidad"]
INTENSITY_COL = FEATURE_NAMES.index("intensidad")  # mapa usado para elegir el cluster tumor

# Cada feature va a la PRIMERA familia cuya palabra clave aparezca en su nombre.
FAMILIAS = {
    "wavelets": ["wav", "dwt"],
    "asimetria": ["asim", "simetr"],
    "gradientes": ["grad", "sobel", "laplac"],
    "textura": ["gabor", "lbp", "entrop", "glcm", "textur"],
    "estadisticos": ["media", "desv", "mean", "std"],
    "intensidad": ["intens"],
}


def evaluate(pred, gt):
    """Devuelve Dice, IoU, sensibilidad y especificidad sin dividir por cero."""
    pred, gt = np.asarray(pred).astype(bool), np.asarray(gt).astype(bool)
    tp = np.sum(pred & gt)
    fp = np.sum(pred & ~gt)
    fn = np.sum(~pred & gt)
    tn = np.sum(~pred & ~gt)

    def div(a, b, si_cero):
        return a / b if b > 0 else si_cero

    return {
        "Dice": div(2 * tp, 2 * tp + fp + fn, 1.0),
        "IoU": div(tp, tp + fp + fn, 1.0),
        "sensibilidad": div(tp, tp + fn, np.nan),
        "especificidad": div(tn, tn + fp, np.nan),
    }


def indices_por_familia(nombres):
    """Agrupa los índices de columnas de FEATURE_NAMES por familia usando palabras clave."""
    familias = {f: [] for f in FAMILIAS}
    for i, nombre in enumerate(nombres):
        n = nombre.lower()
        fam = next((f for f, claves in FAMILIAS.items() if any(c in n for c in claves)), None)
        if fam:
            familias[fam].append(i)
    return familias


def procesar_corte(img_path, mask_path, idx_sel, familias):
    """Corre línea base, método propuesto y ablation sobre un corte; devuelve un dict de métricas."""
    gt = load_mask(mask_path) > 0
    raw = load_flair(img_path)                 # imagen cruda (la línea base la necesita así)
    brain = brain_mask(raw)                    # cerebro explícito para k-means
    feats = compute_features(preprocess(raw))  # (H, W, n_features), una sola vez
    ref = feats[..., INTENSITY_COL]            # mapa con el que se elige el cluster tumor

    def proponer(cols):
        return postprocess(segment(feats[..., cols], brain=brain, ref=ref))

    fila = {}
    # Línea base: Otsu sobre la imagen cruda + mismo posprocesamiento que el propuesto
    for k, v in evaluate(postprocess(segment_baseline(raw)), gt).items():
        fila[f"baseline_{k}"] = v
    # Método propuesto
    for k, v in evaluate(proponer(idx_sel), gt).items():
        fila[f"propuesto_{k}"] = v
    # Ablation: sacar una familia completa de las features elegidas
    for fam, ids in familias.items():
        resto = [i for i in idx_sel if i not in ids]
        if len(resto) == len(idx_sel) or not resto:
            continue
        fila[f"sin_{fam}"] = evaluate(proponer(resto), gt)["Dice"]
    return fila


def correr_validacion(n_cortes=None):
    """Evalúa sobre cortes con tumor (todos o una muestra); devuelve tabla por corte."""
    idx = build_index()
    idx = idx[idx["has_tumor"]]
    if n_cortes is not None:
        idx = idx.sample(n=min(n_cortes, len(idx)), random_state=SEED)

    idx_sel = [FEATURE_NAMES.index(n) for n in SELECTED_FEATURES]
    familias = indices_por_familia(FEATURE_NAMES)
    print("Features seleccionadas:", SELECTED_FEATURES)
    print("Familias:", {f: [FEATURE_NAMES[i] for i in ids] for f, ids in familias.items()})

    filas = [procesar_corte(r["img_path"], r["mask_path"], idx_sel, familias)
             for _, r in idx.iterrows()]
    df = pd.DataFrame(filas)
    df.insert(0, "patient", idx["patient"].values)
    df.insert(1, "slice", idx["slice"].values)
    return df


def tabla_resumen(df):
    """Media y desvío de cada métrica para línea base y propuesto."""
    return pd.DataFrame([
        {"metodo": m, "metrica": k, "media": df[f"{m}_{k}"].mean(), "desvio": df[f"{m}_{k}"].std()}
        for m in ["baseline", "propuesto"] for k in METRICAS
    ])


def tabla_ablation(df):
    """Dice medio del método completo y sin cada familia, con la diferencia respecto al completo."""
    completo = df["propuesto_Dice"].mean()
    filas = [{"configuracion": "completo", "dice_media": completo,
              "dice_desvio": df["propuesto_Dice"].std(), "delta": 0.0}]
    for c in [c for c in df.columns if c.startswith("sin_")]:
        filas.append({"configuracion": c, "dice_media": df[c].mean(),
                      "dice_desvio": df[c].std(), "delta": df[c].mean() - completo})
    return pd.DataFrame(filas)


def dice_por_clinico(df):
    """Dice medio por tumor_location y por neoplasm_histologic_grade (opcional)."""
    clin = pd.read_csv(DATA_DIR / "data.csv").rename(columns={"Patient": "patient"})
    df = df.merge(clin, on="patient", how="left")
    out = {}
    for col in ["tumor_location", "neoplasm_histologic_grade"]:
        if col in df.columns:
            out[col] = df.groupby(col)[["baseline_Dice", "propuesto_Dice"]].agg(["mean", "count"]).round(3)
    return out


def boxplot_dice(df, ruta):
    """Boxplot del Dice por corte: línea base vs propuesto."""
    fig, ax = plt.subplots(figsize=(4, 5))
    ax.boxplot([df["baseline_Dice"], df["propuesto_Dice"]])
    ax.set_xticklabels(["Baseline (Otsu)", "Propuesto (k-means)"])
    ax.set_ylabel("Dice")
    ax.set_title("Dice por corte con tumor")
    fig.tight_layout()
    fig.savefig(ruta, dpi=150)
    plt.close(fig)


if __name__ == "__main__":
    out = Path("results")
    out.mkdir(exist_ok=True)

    df = correr_validacion(n_cortes=100)  # None para usar todos los cortes
    df.to_csv(out / "etapa5_metricas_por_corte.csv", index=False)

    resumen = tabla_resumen(df)
    resumen.to_csv(out / "etapa5_resumen.csv", index=False)
    print(resumen.round(3).to_string(index=False))

    boxplot_dice(df, out / "etapa5_boxplot_dice.png")

    ablation = tabla_ablation(df)
    ablation.to_csv(out / "etapa5_ablation.csv", index=False)
    print(ablation.round(3).to_string(index=False))

    if (DATA_DIR / "data.csv").exists():
        for col, tabla in dice_por_clinico(df).items():
            tabla.to_csv(out / f"etapa5_dice_por_{col}.csv")