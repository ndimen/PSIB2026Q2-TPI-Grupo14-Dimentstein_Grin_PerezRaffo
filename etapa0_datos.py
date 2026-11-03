# etapa0_datos.py - Etapa 0: cargar datos y explorarlos
# Uso (desde la raíz del repo):  python etapa0_datos.py
import re
from pathlib import Path

import matplotlib
matplotlib.use("Agg")  # backend sin ventanas: solo guardamos archivos
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import tifffile

DATA_DIR = Path("data")  # carpeta con una subcarpeta por paciente (si hay una intermedia, se corrige acá)
SEED = 42                # semilla fija


def load_flair(path):
    """Devuelve el canal FLAIR (índice 1) del .tif como float32 2D."""
    img = tifffile.imread(path)
    return img[..., 1].astype(np.float32)  # el .tif viene como (H, W, 3)


def load_mask(path):
    """Devuelve la máscara como uint8 2D con valores 0/1 (sirve si viene 0/255)."""
    return (np.squeeze(tifffile.imread(path)) > 0).astype(np.uint8)


def build_index():
    """DataFrame con una fila por corte: patient, slice, img_path, mask_path, tumor_area, has_tumor."""
    rows = []
    # Las carpetas se descubren listando data/ (se ignoran data.csv, README, etc.)
    for folder in sorted(DATA_DIR.glob("TCGA_*")):
        if not folder.is_dir():
            continue
        patient = "_".join(folder.name.split("_")[:3])  # TCGA_CS_4941_19960909 -> TCGA_CS_4941
        for img in folder.glob("*.tif"):
            # Esta regex solo matchea imágenes (terminan en _<corte>.tif); las máscaras terminan en _mask.tif
            m = re.search(r"_(\d+)\.tif$", img.name)
            if m is None:
                continue
            mask = img.with_name(f"{img.stem}_mask.tif")  # la máscara del mismo corte
            if not mask.exists():
                print(f"AVISO: falta la máscara de {img.name}")
                continue
            area = int(load_mask(mask).sum())  # píxeles de tumor
            rows.append((patient, int(m.group(1)), str(img), str(mask), area, area > 0))
    cols = ["patient", "slice", "img_path", "mask_path", "tumor_area", "has_tumor"]
    # Ordenamos por paciente y por corte como ENTERO (7 < 10)
    return pd.DataFrame(rows, columns=cols).sort_values(["patient", "slice"]).reset_index(drop=True)


def load_clinical(index):
    """Lee data/data.csv y lo une al índice por patient, avisando los que no matchean."""
    clin = pd.read_csv(DATA_DIR / "data.csv").rename(columns={"Patient": "patient"})
    sin_clinica = set(index["patient"]) - set(clin["patient"])
    sin_imagenes = set(clin["patient"]) - set(index["patient"])
    if sin_clinica:
        print("AVISO: pacientes con imágenes pero sin fila en data.csv:", sorted(sin_clinica))
    if sin_imagenes:
        print("AVISO: pacientes en data.csv sin imágenes:", sorted(sin_imagenes))
    return index.merge(clin, on="patient", how="left")  # left: no perdemos cortes


if __name__ == "__main__":
    out = Path("results/eda")
    out.mkdir(parents=True, exist_ok=True)
    idx = load_clinical(build_index())

    # 1. Cortes por paciente y % de cortes con tumor por paciente (tabla + figura)
    pac = idx.groupby("patient").agg(cortes=("slice", "size"), pct_tumor=("has_tumor", lambda x: 100 * x.mean()))
    pac.round(1).to_csv(out / "pacientes.csv")
    fig, ax = plt.subplots(1, 2, figsize=(10, 4))
    ax[0].hist(pac["cortes"], bins=20)
    ax[0].set_title("Cortes por paciente")
    ax[1].hist(pac["pct_tumor"], bins=20)
    ax[1].set_title("% de cortes con tumor por paciente")
    plt.savefig(out / "cortes_y_tumor_por_paciente.png", dpi=150, bbox_inches="tight")
    plt.close()

    # 2. Distribución del área del tumor (solo cortes con tumor)
    areas = idx.loc[idx["has_tumor"], "tumor_area"]
    areas.describe().to_csv(out / "area_tumor.csv")
    plt.hist(areas, bins=40)
    plt.xlabel("Área del tumor (píxeles)")
    plt.ylabel("Cortes")
    plt.savefig(out / "hist_area_tumor.png", dpi=150, bbox_inches="tight")
    plt.close()

    # 3. Intensidades del FLAIR: muestra de 200 cortes, sin el fondo (valor 0)
    muestra = idx.sample(min(200, len(idx)), random_state=SEED)
    imgs = [load_flair(p) for p in muestra["img_path"]]
    pix = np.concatenate([im[im > 0] for im in imgs])
    pd.Series(pix).describe(percentiles=[0.01, 0.5, 0.99]).to_csv(out / "intensidades.csv")
    plt.hist(pix, bins=100)
    plt.yscale("log")
    plt.xlabel("Intensidad FLAIR")
    plt.savefig(out / "hist_intensidades.png", dpi=150, bbox_inches="tight")
    plt.close()

    # 4. Tres ejemplos con el borde de la máscara en rojo
    fig, ax = plt.subplots(1, 3, figsize=(12, 4))
    for a, (_, f) in zip(ax, idx[idx["has_tumor"]].sample(3, random_state=SEED).iterrows()):
        a.imshow(load_flair(f["img_path"]), cmap="gray")
        a.contour(load_mask(f["mask_path"]), levels=[0.5], colors="r")
        a.set_title(f"{f['patient']} corte {f['slice']}", fontsize=9)
        a.axis("off")
    plt.savefig(out / "ejemplos.png", dpi=150, bbox_inches="tight")
    plt.close()

    # Resumen por consola
    print(f"Pacientes: {idx['patient'].nunique()} | Cortes: {len(idx)} | Con tumor: {idx['has_tumor'].mean():.1%}")
    print(f"Área mediana del tumor: {areas.median():.0f} px | Rango FLAIR: {pix.min():.0f} a {pix.max():.0f}")
    print(f"Resultados guardados en {out}/")