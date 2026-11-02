# etapa5_validacion.py
# Validación: métricas, línea base (Otsu) vs método propuesto (k-means), ablation por familia
# y promedio opcional por variables clínicas. Sin split train/test (análisis exploratorio).
from pathlib import Path

import matplotlib
matplotlib.use("Agg")  # backend sin ventana: solo guardamos figuras
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import pywt
from scipy import ndimage as ndi

from cargadatos import build_index, load_flair, load_mask   # TODO: renombrar a etapa0_datos cuando se unifique
from procesamiento import brain_mask, preprocess            # TODO: renombrar a etapa1_preprocesamiento
from etapa4_segmentacion import segment_baseline, segment, postprocess

SEED = 42
METRICAS = ["Dice", "IoU", "sensibilidad", "especificidad"]

# Familias de features: cada feature va a la PRIMERA familia cuya palabra clave aparezca en su nombre
# (en minúsculas). AJUSTAR a los nombres reales de FEATURE_NAMES cuando exista la etapa 2.
FAMILIAS = {
    "wavelets": ["wav", "dwt"],
    "asimetria": ["asim", "simetr"],
    "gradientes": ["grad", "sobel", "laplac"],
    "textura": ["glcm", "lbp", "textur", "entrop", "contrast", "homog"],
    "estadisticos": ["mean", "media", "std", "desv", "var", "skew", "kurt", "local"],
    "intensidad": ["intens", "rel", "flair"],
}
# segment() elige el cluster tumor con la columna 0, así que esa familia va primero y no se ablaciona
FAMILIA_REF = "intensidad"

# ---------------------------------------------------------------------------
# Dependencias que todavía pueden no existir (etapas 2 y 3)
# ---------------------------------------------------------------------------
try:
    from etapa2_mapas import compute_features, FEATURE_NAMES
except ModuleNotFoundError as e:
    # Solo usamos el mock si falta el archivo de la etapa 2 (no si falla un import interno)
    if e.name != "etapa2_mapas":
        raise
    print("AVISO: usando MOCK de etapa2_mapas (TODO: reemplazar por el real)")
    FEATURE_NAMES = ["intensidad_rel", "media_local", "std_local", "grad_sobel",
                     "textura_rango_local", "asim_hemisferica", "wav_detalle"]

    def compute_features(img):
        """MOCK de la etapa 2: 7 mapas simples (uno o dos por familia) con forma (H, W, 7)."""
        img = img.astype(float)
        # Intensidad relativa: imagen dividida por la mediana de los píxeles del cerebro (>0)
        cerebro = img[img > 0]
        rel = img / (np.median(cerebro) if cerebro.size else 1.0)
        # Estadísticos locales: media y desvío en ventana 7x7 (E[x²]-E[x]²)
        media = ndi.uniform_filter(img, 7)
        std = np.sqrt(np.maximum(ndi.uniform_filter(img ** 2, 7) - media ** 2, 0))
        # Gradiente: magnitud de Sobel
        grad = np.hypot(ndi.sobel(img, 0), ndi.sobel(img, 1))
        # Textura (aprox.): rango local = máximo - mínimo en ventana 5x5
        rango = ndi.maximum_filter(img, 5) - ndi.minimum_filter(img, 5)
        # Asimetría: diferencia con la imagen espejada izquierda-derecha (supone cerebro centrado)
        asim = np.abs(img - img[:, ::-1])
        # Wavelet: magnitud de los detalles de Haar de un nivel, reescalada al tamaño original
        _, (cH, cV, cD) = pywt.dwt2(img, "haar")
        det = np.sqrt(cH ** 2 + cV ** 2 + cD ** 2)
        det = ndi.zoom(det, (img.shape[0] / det.shape[0], img.shape[1] / det.shape[1]), order=1)
        return np.stack([rel, media, std, grad, rango, asim, det], axis=-1)

try:
    from etapa3_seleccion import SELECTED_FEATURES
except ModuleNotFoundError as e:
    if e.name != "etapa3_seleccion":
        raise
    print("AVISO: usando MOCK de etapa3_seleccion (TODO: se usan todas las features)")
    SELECTED_FEATURES = list(FEATURE_NAMES)


def evaluate(pred, gt):
    """Devuelve Dice, IoU, sensibilidad y especificidad sin dividir por cero."""
    # Pasamos a booleano para contar píxeles con operaciones vectorizadas
    pred, gt = np.asarray(pred).astype(bool), np.asarray(gt).astype(bool)
    tp = np.sum(pred & gt)    # tumor predicho y real
    fp = np.sum(pred & ~gt)   # predicho pero no es tumor
    fn = np.sum(~pred & gt)   # tumor real que se perdió
    tn = np.sum(~pred & ~gt)  # fondo correcto

    # Si el denominador es 0 (ambas máscaras vacías) Dice/IoU valen 1; sens/espec quedan en NaN
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
        # next(...) toma la primera familia que coincide; None si ninguna
        fam = next((f for f, claves in FAMILIAS.items() if any(c in n for c in claves)), None)
        if fam:
            familias[fam].append(i)
    return familias


def procesar_corte(img_path, mask_path, idx_sel, familias):
    """Corre línea base, método propuesto y ablation sobre un corte; devuelve un dict de métricas."""
    gt = load_mask(mask_path) > 0         # máscara real binaria
    raw = load_flair(img_path)            # imagen cruda: la línea base y brain_mask la necesitan así
    brain = brain_mask(raw)               # máscara de cerebro, se pasa a segment para no inferirla
    feats = compute_features(preprocess(raw))   # (H, W, n_features), se calcula una sola vez

    fila = {}
    # Línea base: Otsu sobre la imagen cruda, con el mismo posprocesamiento que el propuesto
    for k, v in evaluate(postprocess(segment_baseline(raw)), gt).items():
        fila[f"baseline_{k}"] = v
    # Método propuesto: k-means sobre las features elegidas + morfología
    for k, v in evaluate(postprocess(segment(feats[..., idx_sel], brain=brain)), gt).items():
        fila[f"propuesto_{k}"] = v
    # Ablation: mismo método sacando de las features elegidas todas las de una familia
    for fam, ids in familias.items():
        resto = [i for i in idx_sel if i not in ids]
        # Se omite la familia de referencia (segment la necesita en la columna 0), las que no
        # estaban en la selección y las que dejarían el conjunto vacío
        if fam == FAMILIA_REF or len(resto) == len(idx_sel) or not resto:
            continue
        pred = postprocess(segment(feats[..., resto], brain=brain))
        fila[f"sin_{fam}"] = evaluate(pred, gt)["Dice"]
    return fila


def correr_validacion(n_cortes=None):
    """Evalúa sobre cortes con tumor (todos si n_cortes=None, o una muestra); devuelve tabla por corte."""
    idx = build_index()
    idx = idx[idx["has_tumor"]]           # solo cortes con tumor real
    # Muestra reproducible si se pidió un subconjunto
    if n_cortes is not None:
        idx = idx.sample(n=min(n_cortes, len(idx)), random_state=SEED)

    familias = indices_por_familia(FEATURE_NAMES)
    # Posiciones de las features seleccionadas; las de intensidad van primero porque
    # segment() usa la columna 0 para decidir cuál cluster es el tumor
    idx_sel = [list(FEATURE_NAMES).index(n) for n in SELECTED_FEATURES]
    idx_sel.sort(key=lambda i: i not in familias[FAMILIA_REF])   # sort estable: solo mueve las de intensidad
    if not idx_sel or idx_sel[0] not in familias[FAMILIA_REF]:
        raise ValueError("SELECTED_FEATURES debe incluir al menos una feature de intensidad")

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


def dice_por_clinico(df, csv_path="data/data.csv"):
    """Dice medio por tumor_location y por neoplasm_histologic_grade (opcional)."""
    clin = pd.read_csv(csv_path)
    # La carpeta es TCGA_CS_4941_19960909; en data.csv el id es TCGA_CS_4941 (sin fecha)
    df = df.assign(Patient=df["patient"].str.split("_").str[:3].str.join("_"))
    df = df.merge(clin, on="Patient", how="left")
    return {col: df.groupby(col)[["baseline_Dice", "propuesto_Dice"]].agg(["mean", "count"]).round(3)
            for col in ["tumor_location", "neoplasm_histologic_grade"]}


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
    # Demo: muestra de cortes con tumor (poner None para usar todos). Con 20 es una prueba rápida.
    out = Path("results")
    out.mkdir(exist_ok=True)

    df = correr_validacion(n_cortes=20)
    df.to_csv(out / "etapa5_metricas_por_corte.csv", index=False)

    resumen = tabla_resumen(df)
    resumen.to_csv(out / "etapa5_resumen.csv", index=False)
    print(resumen.round(3).to_string(index=False))

    boxplot_dice(df, out / "etapa5_boxplot_dice.png")

    ablation = tabla_ablation(df)
    ablation.to_csv(out / "etapa5_ablation.csv", index=False)
    print(ablation.round(3).to_string(index=False))

    # Opcional: promedio por variables clínicas (se omite si no está data.csv)
    if Path("data/data.csv").exists():
        for col, tabla in dice_por_clinico(df).items():
            tabla.to_csv(out / f"etapa5_dice_por_{col}.csv")