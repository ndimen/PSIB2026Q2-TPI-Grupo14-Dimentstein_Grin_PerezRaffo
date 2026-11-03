# Librerías estándar para rutas
import os

import matplotlib
matplotlib.use("Agg")  # backend sin ventana: solo guardamos figuras, nunca plt.show
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from sklearn.metrics import roc_auc_score

# Etapa 0 (Nico): índice de datos y carga; etapa 1: preprocesamiento; etapa 2 (Rama): mapas
from etapa0_datos import build_index, load_flair, load_mask
from etapa1_preprocesamiento import preprocess
from etapa2_mapas import FEATURE_NAMES, compute_features

# Semilla fija para que todo sea reproducible
SEED = 42
np.random.seed(SEED)

# Parámetros del análisis (se pueden cambiar sin tocar las funciones)
N_PATIENTS = 20          # cantidad de pacientes a muestrear
SLICES_PER_PATIENT = 5   # cortes con tumor por paciente (limita el tiempo de cómputo)
N_PIX = 500              # máximo de píxeles tumor y de píxeles sanos por corte
MIN_TUMOR = 50           # un corte "tiene tumor" si su máscara tiene al menos estos píxeles
R_MAX = 0.9              # umbral de |correlación| para descartar features redundantes
RANKING_CSV = "results/etapa3_ranking.csv"


def pick_slices(index, n_patients=N_PATIENTS, per_patient=SLICES_PER_PATIENT, seed=SEED):
    """Elige n_patients pacientes al azar y, de cada uno, cortes con tumor; devuelve [(img, mask)]."""
    rng = np.random.default_rng(seed)
    patients = sorted(index["patient"].unique())  # pacientes descubiertos por build_index
    patients = rng.choice(patients, size=min(n_patients, len(patients)), replace=False)
    chosen = []
    for p in patients:
        rows = index[index["patient"] == p]  # todos los cortes del paciente
        # Nos quedamos con los cortes cuya máscara tiene tumor suficiente
        has_tumor = np.array([(load_mask(m) > 0).sum() >= MIN_TUMOR for m in rows["mask_path"]])
        rows = rows[has_tumor]
        rows = rows.sample(min(per_patient, len(rows)), random_state=seed)  # submuestra reproducible
        chosen += list(zip(rows["img_path"], rows["mask_path"]))
    return chosen


def sample_pixels(slices, n_pix=N_PIX, seed=SEED):
    """Calcula los mapas de cada corte y muestrea hasta n_pix píxeles tumor y n_pix sanos; devuelve X, y."""
    rng = np.random.default_rng(seed)
    X, y = [], []
    for img_path, mask_path in slices:
        raw = load_flair(img_path)  # FLAIR crudo (el fondo vale 0)
        mask = load_mask(mask_path) > 0  # máscara del tumor (bool)
        feats = compute_features(preprocess(raw)).reshape(-1, len(FEATURE_NAMES))  # (H*W, n_features)
        brain = raw > 0  # "sano" = cerebro sin tumor (el fondo negro inflaría el AUC)
        for label, region in ((1, mask), (0, brain & ~mask)):
            candidates = np.flatnonzero(region.ravel())  # índices planos de la región
            idx = rng.choice(candidates, size=min(n_pix, len(candidates)), replace=False)
            X.append(feats[idx])  # valores de los mapas en esos píxeles
            y.append(np.full(len(idx), label))  # 1 = tumor, 0 = sano
    return np.vstack(X), np.concatenate(y)


def auc_per_feature(X, y):
    """AUC de cada feature como max(auc, 1-auc), ordenado de mayor a menor."""
    aucs = np.array([roc_auc_score(y, X[:, k]) for k in range(X.shape[1])])  # un AUC por mapa
    aucs = np.maximum(aucs, 1 - aucs)  # no importa si el tumor es más alto o más bajo que el sano
    return pd.Series(aucs, index=FEATURE_NAMES, name="auc").sort_values(ascending=False)


def select_features(auc, corr, r_max=R_MAX):
    """Recorre las features de mejor a peor AUC y descarta las que tienen |r| > r_max con una ya elegida."""
    kept = []
    for f in auc.index:  # el orden es el del ranking
        if all(abs(corr.loc[f, k]) <= r_max for k in kept):  # no redundante con las ya elegidas
            kept.append(f)
    return kept


def load_selected():
    """Lee las features elegidas del último ranking guardado; si no existe, usa todas."""
    if os.path.exists(RANKING_CSV):
        df = pd.read_csv(RANKING_CSV)
        return df.loc[df["seleccionada"], "feature"].tolist()
    return list(FEATURE_NAMES)  # hasta correr este archivo una vez, se usan todas las features


# Lista de nombres que importan las demás etapas (from etapa3_seleccion import SELECTED_FEATURES)
SELECTED_FEATURES = load_selected()


if __name__ == "__main__":
    os.makedirs("results", exist_ok=True)  # carpeta de salida

    # 1) Elegimos cortes con tumor y muestreamos píxeles tumor/sano
    index = build_index()  # build_index de la etapa 0 no recibe argumentos
    slices = pick_slices(index)
    X, y = sample_pixels(slices)
    print(f"Cortes: {len(slices)} | píxeles: {len(y)} (tumor: {int(y.sum())}, sano: {int((1 - y).sum())})")

    # 2) AUC por feature, matriz de correlación y selección
    auc = auc_per_feature(X, y)
    corr = pd.DataFrame(np.corrcoef(X, rowvar=False), index=FEATURE_NAMES, columns=FEATURE_NAMES)
    selected = select_features(auc, corr)

    # 3) Ranking en CSV (con la marca de las features seleccionadas)
    ranking = auc.rename_axis("feature").reset_index()
    ranking["seleccionada"] = ranking["feature"].isin(selected)
    ranking.to_csv(RANKING_CSV, index=False)

    # 4) Boxplots tumor vs sano, uno por feature (cada mapa tiene su propia escala)
    n_cols = 4
    n_rows = int(np.ceil(len(FEATURE_NAMES) / n_cols))
    fig, axs = plt.subplots(n_rows, n_cols, figsize=(3.5 * n_cols, 3 * n_rows))
    for ax, k, name in zip(axs.ravel(), range(len(FEATURE_NAMES)), FEATURE_NAMES):
        ax.boxplot([X[y == 1, k], X[y == 0, k]], showfliers=False)  # sin outliers para ver mejor
        ax.set_xticklabels(["tumor", "sano"])
        ax.set_title(f"{name} (AUC {auc[name]:.2f})", fontsize=9)
    for ax in axs.ravel()[len(FEATURE_NAMES):]:
        ax.axis("off")  # oculta los ejes sobrantes de la grilla
    fig.tight_layout()
    fig.savefig("results/etapa3_boxplots.png", dpi=120)
    plt.close(fig)

    # 5) Matriz de correlación entre features
    fig, ax = plt.subplots(figsize=(8, 7))
    im = ax.imshow(corr.values, vmin=-1, vmax=1, cmap="coolwarm")
    ax.set_xticks(range(len(FEATURE_NAMES)))
    ax.set_xticklabels(FEATURE_NAMES, rotation=90)
    ax.set_yticks(range(len(FEATURE_NAMES)))
    ax.set_yticklabels(FEATURE_NAMES)
    fig.colorbar(im, label="correlación de Pearson")
    fig.tight_layout()
    fig.savefig("results/etapa3_correlacion.png", dpi=120)
    plt.close(fig)

    # 6) Resumen por consola
    print(ranking.to_string(index=False))
    print("SELECTED_FEATURES:", selected)
    print("Guardado en results/: etapa3_ranking.csv, etapa3_boxplots.png, etapa3_correlacion.png")