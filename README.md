# PSIB2026Q2-TPI-Grupo14-Dimentstein Grin Pérez Raffo

**Segmentación de tumores cerebrales en MRI FLAIR guiada por mapas de características**

Trabajo Práctico de Imágenes (TPI) de 16.63 Procesamiento de Señales e Imágenes Biomédicas (ITBA, 2C 2026), Grupo 14.

Integrantes: Nicolás Dimentstein, Ramiro Grin y Joaquín Hernán Pérez Raffo.

## Descripción

El proyecto estudia qué mapas de características (intensidad, estadísticos locales, gradientes, textura, wavelets y asimetría entre hemisferios) discriminan el tumor en cortes FLAIR de gliomas de bajo grado, y cuánto mejoran la segmentación frente a una línea base simple.

Se comparan tres métodos:

1. **Línea base:** umbral de Otsu dentro del cerebro.
2. **k-means:** agrupamiento sobre los mapas seleccionados por su poder discriminante.
3. **k-means + Chan-Vese:** el resultado del k-means con el borde refinado por un contorno activo de Chan-Vese.

La segmentación se valida contra las máscaras manuales con Dice, IoU, sensibilidad y especificidad, incluye un estudio de ablación por familia de mapas y termina con la extracción de descriptores morfológicos y de intensidad del tumor.

## Dataset

Se usa el *LGG Segmentation Dataset* (Buda et al.), disponible en Kaggle:
<https://www.kaggle.com/datasets/mateuszbuda/lgg-mri-segmentation>

Contenido:

- 110 pacientes de la colección TCGA-LGG.
- Una carpeta por paciente con pares `TCGA_..._<corte>.tif` (256 × 256, 3 canales: pre-contraste, FLAIR y post-contraste; se usa solo el FLAIR) y `TCGA_..._<corte>_mask.tif` (máscara manual del tumor).
- `data.csv` con datos clínicos y genómicos por paciente.

**Ubicación esperada.** El dataset no se sube al repositorio. Hay que descargarlo y descomprimirlo de modo que las carpetas de pacientes y `data.csv` queden directamente dentro de `data/`:

```
data/
├── data.csv
├── TCGA_CS_4941_19960909/
│   ├── TCGA_CS_4941_19960909_1.tif
│   ├── TCGA_CS_4941_19960909_1_mask.tif
│   └── ...
└── ...
```

## Estructura del repositorio

| Archivo | Contenido |
|---|---|
| `etapa0_datos.py` | Carga del FLAIR y de las máscaras, índice de cortes (`build_index`), unión con `data.csv` y análisis exploratorio. |
| `etapa1_preprocesamiento.py` | Máscara de cerebro, comparación de filtros (mediana, gaussiano, bilateral, NLM), z-score, `preprocess` y análisis de compresión JPEG. |
| `etapa2_mapas.py` | `compute_features`: 12 mapas por píxel (intensidad, media y desvío locales, entropía, Sobel, Laplaciano, LBP, 3 Gabor, wavelet y asimetría). |
| `etapa3_seleccion.py` | AUC de cada mapa (tumor vs. cerebro sano), filtro por AUC mínimo, eliminación de mapas redundantes y `SELECTED_FEATURES`. |
| `etapa4_segmentacion.py` | `segment_baseline` (Otsu), `segment` (k-means), `postprocess` (morfología) y `refine_chan_vese` (refinamiento del borde). |
| `etapa5_validacion.py` | `evaluate` (Dice, IoU, sensibilidad, especificidad), comparación de los tres métodos, ablation y Dice por subgrupo clínico. |
| `etapa6_descriptores.py` | `compute_descriptors`: forma e intensidad del tumor con la máscara real y la predicha, y su concordancia. |
| `figuras_informe.py` | Tests de Wilcoxon, análisis por tamaño de tumor y figuras del informe. |
| `interfaz/` | Interfaz gráfica (ver [`interfaz/README.md`](interfaz/README.md)). |
| `results/` | Tablas (CSV) y figuras generadas por cada etapa. |

Cada etapa es un único archivo `.py` con sus funciones y un bloque `if __name__ == "__main__"` que corre una demo y guarda sus resultados en `results/`. Las etapas se importan entre sí por nombre (por ejemplo, `from etapa0_datos import load_flair`).

## Instalación

Requiere Python 3.10 o superior.

```bash
python -m venv .venv
source .venv/bin/activate          # en Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

## Ejecución

Todos los comandos se corren **desde la raíz del repositorio**, porque las rutas `data/` y `results/` son relativas.

```bash
python etapa0_datos.py             # análisis exploratorio            -> results/eda/
python etapa1_preprocesamiento.py  # filtros y compresión             -> results/etapa1_*
python etapa2_mapas.py             # mapas de un corte de ejemplo     -> results/etapa2_*
python etapa3_seleccion.py         # ranking y selección de mapas     -> results/etapa3_*
python etapa4_segmentacion.py      # ejemplo de segmentación          -> results/etapa4_*
python etapa5_validacion.py        # validación y ablation            -> results/etapa5_*
python etapa6_descriptores.py      # descriptores del tumor           -> results/etapa6_*
python figuras_informe.py          # tests y figuras del informe      -> results/informe/
```

**Orden obligatorio.** `etapa3_seleccion.py` tiene que correrse antes que las etapas 5 y 6 y que la interfaz, porque guarda en `results/etapa3_ranking.csv` la lista de mapas seleccionados que esas etapas leen. Si ese archivo no existe, se usan los 12 mapas.

Tiempos aproximados: la etapa 3 tarda alrededor de 1 minuto, la 5 (100 cortes) alrededor de 1 minuto y la 6 (200 cortes) algunos minutos más. El resto tarda segundos.

## Interfaz gráfica

```bash
python interfaz/main_window.py
```

Permite elegir paciente y corte (o abrir un `.tif`), preprocesar, visualizar los 12 mapas, segmentar con los tres métodos y calcular métricas y descriptores, con exportación a CSV. Los detalles están en [`interfaz/README.md`](interfaz/README.md).

## Resultados principales

Sobre 100 cortes con tumor (57 pacientes):

| Método | Dice (media ± desvío) | Sensibilidad | Especificidad |
|---|---|---|---|
| Otsu | 0,521 ± 0,379 | 0,720 | 0,953 |
| k-means | 0,590 ± 0,372 | 0,628 | 0,990 |
| k-means + Chan-Vese | 0,602 ± 0,376 | 0,642 | 0,991 |

Mapas seleccionados: media local, intensidad y asimetría hemisférica. El refinamiento con Chan-Vese mejora significativamente al k-means (Wilcoxon, p < 0,001) y a la línea base (p = 0,027). El análisis completo está en el informe.

## Reproducibilidad

Todas las semillas aleatorias están fijadas en 42.
