# figuras_informe.py - Figuras y estadística adicionales para el informe del TPI
# Uso (desde la raíz del repo, después de correr etapa3 y etapa5):  python figuras_informe.py
# Lee los CSV de results/ y guarda en results/informe/ las figuras y tablas que usa el informe.
from pathlib import Path

import matplotlib
matplotlib.use("Agg")  # backend sin ventanas: solo guardamos archivos
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scipy.stats import wilcoxon

from etapa0_datos import build_index, load_flair, load_mask
from etapa1_preprocesamiento import brain_mask, preprocess
from etapa2_mapas import FEATURE_NAMES, compute_features
from etapa3_seleccion import SELECTED_FEATURES
from etapa4_segmentacion import postprocess, refine_chan_vese, segment, segment_baseline

OUT = Path("results/informe")
IDX_SEL = [FEATURE_NAMES.index(n) for n in SELECTED_FEATURES]
IDX_INT = FEATURE_NAMES.index("intensidad")
plt.rcParams.update({"font.size": 9, "axes.spines.top": False, "axes.spines.right": False})


METODOS = {"baseline": "Otsu", "propuesto": "k-means", "propuesto_cv": "k-means + CV"}
PARES = [("baseline", "propuesto"), ("propuesto", "propuesto_cv"), ("baseline", "propuesto_cv")]


def tests_pareados(df):
    """Wilcoxon pareado entre cada par de métodos por métrica, y método completo vs cada ablation."""
    filas = []
    for m in ["Dice", "IoU", "sensibilidad", "especificidad"]:
        for x, y in PARES:
            a, b = df[f"{x}_{m}"], df[f"{y}_{m}"]
            filas.append({"comparacion": f"{m}: {METODOS[x]} vs {METODOS[y]}", "mediana_1": a.median(),
                          "mediana_2": b.median(), "p": wilcoxon(a, b).pvalue})
    for c in [c for c in df if c.startswith("sin_")]:
        filas.append({"comparacion": f"Dice: completo vs {c}", "mediana_1": df["propuesto_Dice"].median(),
                      "mediana_2": df[c].median(), "p": wilcoxon(df["propuesto_Dice"], df[c]).pvalue})
    return pd.DataFrame(filas)


def fig_auc_ablation(ranking, ablation):
    """(a) AUC por mapa, marcando los seleccionados; (b) cambio de Dice al quitar cada familia."""
    fig, (a1, a2) = plt.subplots(1, 2, figsize=(9, 3.2), gridspec_kw={"width_ratios": [1.3, 1]})
    r = ranking.iloc[::-1]                                         # mejor arriba
    colores = np.where(r["seleccionada"], "#2b6cb0", "#a0aec0")    # gris = descartada por redundancia
    a1.barh(r["feature"], r["auc"], color=colores)
    a1.set_xlim(0.5, 1)
    a1.set_xlabel("AUC (tumor vs. cerebro sano)")
    a1.set_title("(a) Poder discriminante por mapa", loc="left")
    ab = ablation[ablation["configuracion"] != "completo"].sort_values("delta")
    a2.barh(ab["configuracion"].str.replace("sin_", "sin "), ab["delta"],
            color=np.where(ab["delta"] < 0, "#c53030", "#2f855a"))
    a2.axvline(0, color="k", lw=0.8)
    a2.set_xlabel("ΔDice respecto del método completo")
    a2.set_title("(b) Ablation por familia", loc="left")
    fig.tight_layout()
    fig.savefig(OUT / "fig_auc_ablation.png", dpi=200, bbox_inches="tight")
    plt.close(fig)


def fig_boxplots(df):
    """Dice y sensibilidad por corte de los tres métodos."""
    fig, axs = plt.subplots(1, 2, figsize=(7.5, 2.8))
    for ax, m in zip(axs, ["Dice", "sensibilidad"]):
        ax.boxplot([df[f"{k}_{m}"] for k in METODOS], widths=0.5)
        ax.set_xticks([1, 2, 3], list(METODOS.values()))
        ax.set_title(m.capitalize())
        ax.set_ylim(-0.02, 1.02)
    fig.tight_layout()
    fig.savefig(OUT / "fig_boxplot_metricas.png", dpi=200, bbox_inches="tight")
    plt.close(fig)


def fig_casos(df, idx):
    """Casos con Dice del método final alto, mediano y bajo: GT (rojo), Otsu (amarillo), k-means + CV (celeste)."""
    d = df.sort_values("propuesto_cv_Dice").reset_index(drop=True)
    casos = [d.iloc[-1], d.iloc[len(d) // 2], d.iloc[int(len(d) * 0.1)]]
    fig, axs = plt.subplots(1, 3, figsize=(9, 3.2))
    for ax, c, etiqueta in zip(axs, casos, ["Bueno", "Mediano", "Malo"]):
        fila = idx[(idx["patient"] == c["patient"]) & (idx["slice"] == c["slice"])].iloc[0]
        raw, gt = load_flair(fila["img_path"]), load_mask(fila["mask_path"]) > 0
        feats = compute_features(preprocess(raw))
        brain, ref = brain_mask(raw), feats[..., IDX_INT]
        prop = refine_chan_vese(ref, postprocess(segment(feats[..., IDX_SEL], brain=brain, ref=ref)), brain)
        base = postprocess(segment_baseline(raw))
        ax.imshow(raw, cmap="gray")
        for m, col in ((gt, "r"), (base, "y"), (prop, "deepskyblue")):
            if m.any():
                ax.contour(m, levels=[0.5], colors=col, linewidths=1)
        ax.set_title(f"{etiqueta}: {c['patient']} c{c['slice']}\nDice Otsu {c['baseline_Dice']:.2f} | "
                     f"k-means + CV {c['propuesto_cv_Dice']:.2f}", fontsize=8)
        ax.axis("off")
    fig.tight_layout()
    fig.savefig(OUT / "fig_casos.png", dpi=200, bbox_inches="tight")
    plt.close(fig)


def dice_por_tamano(df, idx):
    """Dice medio por tercil del área del tumor (en píxeles de la máscara real)."""
    d = df.merge(idx[["patient", "slice", "tumor_area"]], on=["patient", "slice"])
    d["tercil"] = pd.qcut(d["tumor_area"], 3, labels=["chico", "medio", "grande"])
    return d.groupby("tercil", observed=True).agg(
        area_min=("tumor_area", "min"), area_max=("tumor_area", "max"), n=("tumor_area", "size"),
        dice_otsu=("baseline_Dice", "mean"), dice_kmeans=("propuesto_Dice", "mean"),
        dice_kmeans_cv=("propuesto_cv_Dice", "mean"))


def fig_pipeline():
    """Diagrama de bloques del pipeline: una caja por etapa con su archivo."""
    etapas = [("Etapa 0", "Carga y EDA", "etapa0_datos.py"), ("Etapa 1", "Preprocesamiento", "etapa1_preprocesamiento.py"),
              ("Etapa 2", "Mapas de\ncaracterísticas", "etapa2_mapas.py"), ("Etapa 3", "Selección\n(AUC, |r|)", "etapa3_seleccion.py"),
              ("Etapa 4", "Segmentación\nOtsu / k-means\n+ Chan-Vese", "etapa4_segmentacion.py"), ("Etapa 5", "Validación\ny ablation", "etapa5_validacion.py"),
              ("Etapa 6", "Descriptores", "etapa6_descriptores.py")]
    fig, ax = plt.subplots(figsize=(10, 1.6))
    w, gap = 1.25, 0.2
    for i, (n, t, f) in enumerate(etapas):
        x = i * (w + gap)
        ax.add_patch(plt.Rectangle((x, 0), w, 1, fc="#ebf4ff", ec="#2b6cb0", lw=1))
        ax.text(x + w / 2, 0.78, n, ha="center", va="center", fontsize=8, weight="bold")
        ax.text(x + w / 2, 0.45, t, ha="center", va="center", fontsize=7.5)
        ax.text(x + w / 2, -0.18, f, ha="center", va="center", fontsize=6, family="monospace", color="#4a5568")
        if i:
            ax.annotate("", xy=(x, 0.5), xytext=(x - gap, 0.5), arrowprops=dict(arrowstyle="->", lw=1))
    ax.set_xlim(-0.05, len(etapas) * (w + gap))
    ax.set_ylim(-0.35, 1.05)
    ax.axis("off")
    fig.savefig(OUT / "fig_pipeline.png", dpi=200, bbox_inches="tight")
    plt.close(fig)


if __name__ == "__main__":
    OUT.mkdir(parents=True, exist_ok=True)
    df = pd.read_csv("results/etapa5_metricas_por_corte.csv")
    idx = build_index()

    tests = tests_pareados(df)
    tests.to_csv(OUT / "wilcoxon.csv", index=False)
    print(tests.to_string(index=False))

    tam = dice_por_tamano(df, idx)
    tam.round(3).to_csv(OUT / "dice_por_tamano.csv")
    print(tam.round(3))

    fig_auc_ablation(pd.read_csv("results/etapa3_ranking.csv"), pd.read_csv("results/etapa5_ablation.csv"))
    fig_boxplots(df)
    fig_pipeline()
    fig_casos(df, idx)
    print(f"Figuras guardadas en {OUT}/")
