# Interfaz gráfica – Segmentación de tumores en MRI FLAIR

Interfaz gráfica hecha con **PySide6** y **pyqtgraph** para ejecutar el pipeline del TPI sobre un corte: cargar un FLAIR, preprocesarlo, calcular los mapas de características, segmentar el tumor con la línea base (Otsu) y con el método propuesto (k-means), y calcular métricas y descriptores.

> La interfaz no reimplementa nada: llama a las funciones de las etapas 0 a 6 que están en la raíz del repo, con los mismos parámetros que usa `etapa5_validacion.py`.

## Requisitos

- Python 3.9 o superior
- Las dependencias de `requirements.txt` (incluye `pyside6` y `pyqtgraph`)
- La carpeta `data/` en la raíz del repo, para navegar el dataset desde las listas. Sin ella, se puede abrir un `.tif` suelto con "Abrir corte".
- Haber corrido `python etapa3_seleccion.py` al menos una vez, para que exista `results/etapa3_ranking.csv` con las features elegidas. Sin ese archivo se usan todas.

## Ejecución

Desde la raíz del repo:

```bash
python interfaz/main_window.py
```

## Archivos

| Archivo | Descripción |
|---|---|
| `ventana.ui` | Diseño de la interfaz, editable con Qt Designer. |
| `ui_ventana.py` | Código Python generado a partir del `.ui`. **No editar a mano**: se sobrescribe al regenerarlo. |
| `main_window.py` | Lógica de la ventana: conexión de botones y llamadas a las etapas del pipeline. |

## Editar la interfaz

```bash
pyside6-designer                                         # Archivo > Abrir > interfaz/ventana.ui (Ctrl+R: vista previa)
pyside6-uic interfaz/ventana.ui -o interfaz/ui_ventana.py   # regenerar después de cada cambio
```

## Organización de la ventana

- **Panel izquierdo:** controles en cinco etapas, en el orden del pipeline. Cada botón se habilita recién cuando se completó el paso anterior.
- **Panel derecho:** pestañas con las imágenes y las tablas.
- **Parte inferior:** registro de eventos y barra de progreso.

Menú **Archivo** (Abrir, Exportar CSV, Salir) y menú **Ayuda** (Acerca de).

### Panel de controles

| Etapa | Widget | Nombre de objeto | Función |
|---|---|---|---|
| 1. Carga de datos | Botón "Abrir corte (.tif)..." | `btnAbrir` | Abre un corte; la máscara `_mask.tif` se busca en la misma carpeta. |
| | Etiqueta | `lblArchivo` | Nombre del corte cargado. |
| | Lista desplegable | `comboPaciente` | Pacientes encontrados en `data/` (`build_index`). |
| | Lista desplegable | `comboCorte` | Cortes del paciente, con el área del tumor; al elegir uno se carga. |
| | Casilla | `chkSoloTumor` | Filtra las listas a cortes con tumor. |
| 2. Preprocesamiento | Botón "Preprocesar" | `btnPreprocesar` | Máscara de cerebro, NLM y z-score (`etapa1`). |
| 3. Mapas | Botón "Calcular mapas" | `btnMapas` | Los 12 mapas de `etapa2` (`compute_features`). |
| | Lista desplegable | `comboMapa` | Mapa a visualizar; marca los elegidos en la etapa 3. |
| 4. Segmentación | Botón "Segmentar (Otsu y k-means)" | `btnSegmentar` | Línea base y método propuesto, con el mismo posprocesamiento (`etapa4`). |
| 5. Resultados | Botón "Calcular métricas" | `btnMetricas` | Dice, IoU, sensibilidad y especificidad (`etapa5`) y descriptores (`etapa6`). |
| | Botón "Exportar CSV" | `btnExportar` | Guarda métricas y descriptores del corte en `results/`. |

### Pestañas de visualización

Las vistas son `GraphicsLayoutWidget` de pyqtgraph: se puede hacer zoom con la rueda y desplazar arrastrando. En la pestaña Segmentación, los tres paneles se mueven juntos.

| Pestaña | Nombre de objeto | Contenido |
|---|---|---|
| Original | `vistaOriginal` | FLAIR crudo con el contorno de la máscara real (rojo). |
| Preprocesada | `vistaPre` | Máscara de cerebro e imagen preprocesada. |
| Mapas | `vistaMapa` | Mapa elegido (colormap viridis) con el contorno real. |
| Segmentación | `vistaSegmentacion` | GT (rojo), Otsu (amarillo) y k-means (verde). |
| Métricas | `tablaMetricas` | Métricas de ambos métodos. |
| Descriptores | `tablaDescriptores` | Descriptores con la máscara real y con la predicha. |

### Parte inferior

`txtLog` (registro de eventos, solo lectura) y `barraProgreso` (avance por etapa del pipeline).

## Flujo de uso

1. Elegir **paciente y corte** en las listas (o **Abrir corte**).
2. **Preprocesar**.
3. **Calcular mapas** y recorrerlos con la lista.
4. **Segmentar**.
5. **Calcular métricas** y, si se quiere, **Exportar CSV**.

## Notas

- Los parámetros (filtro, ventanas de los mapas, cantidad de clusters, radio del posprocesamiento) **no se eligen desde la interfaz**: son los definidos en cada etapa.
- Las features del método propuesto son `SELECTED_FEATURES` de `etapa3_seleccion.py`; el cluster tumor se elige con el mapa de intensidad, igual que en la validación.
- Si se renombra un widget en Designer, hay que actualizarlo también en `main_window.py`.
