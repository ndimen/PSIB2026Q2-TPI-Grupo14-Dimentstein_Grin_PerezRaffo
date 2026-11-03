# main_window.py - Lógica de la interfaz gráfica del TPI (Grupo 14)
# Uso (desde la raíz del repo):  python interfaz/main_window.py
# El diseño está en ventana.ui; ui_ventana.py se genera con:  pyside6-uic interfaz/ventana.ui -o interfaz/ui_ventana.py
import os
import sys
from pathlib import Path

# Las etapas viven en la raíz del repo y usan rutas relativas (data/, results/):
# agregamos la raíz al path y nos paramos ahí, así la interfaz corre desde cualquier carpeta
RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ))
sys.path.insert(0, str(Path(__file__).resolve().parent))
os.chdir(RAIZ)

import numpy as np
import pandas as pd
import pyqtgraph as pg
from PySide6.QtCore import Qt
from PySide6.QtWidgets import (QApplication, QFileDialog, QHeaderView, QMainWindow, QMessageBox, QTableWidgetItem)
from scipy import ndimage as ndi

from etapa0_datos import DATA_DIR, build_index, load_flair, load_mask
from etapa1_preprocesamiento import brain_mask, preprocess
from etapa2_mapas import FEATURE_NAMES, compute_features
from etapa3_seleccion import SELECTED_FEATURES
from etapa4_segmentacion import postprocess, segment, segment_baseline
from etapa5_validacion import METRICAS, evaluate
from etapa6_descriptores import DESCRIPTORS, compute_descriptors
from ui_ventana import Ui_MainWindow

pg.setConfigOptions(imageAxisOrder="row-major", antialias=True)  # imágenes como (fila, columna), igual que numpy

# Colores de los contornos: rojo = máscara real, verde = método, amarillo = línea base
ROJO, VERDE, AMARILLO = (255, 60, 60), (60, 220, 60), (255, 210, 0)
IDX_SEL = [FEATURE_NAMES.index(n) for n in SELECTED_FEATURES]  # columnas que usa el método propuesto
IDX_INT = FEATURE_NAMES.index("intensidad")                    # mapa con el que se elige el cluster tumor


def borde_rgba(mask, color):
    """Imagen RGBA con solo el borde de la máscara pintado (para superponer sobre el FLAIR)."""
    borde = mask & ~ndi.binary_erosion(mask)        # píxeles de la máscara que tocan el exterior
    rgba = np.zeros((*mask.shape, 4), np.uint8)
    rgba[borde] = (*color, 255)                     # opaco en el borde, transparente en el resto
    return rgba


def niveles(img):
    """Niveles de gris robustos (percentiles 1 y 99) para que un píxel extremo no oscurezca la imagen."""
    return np.percentile(img, [1, 99])


class MainWindow(QMainWindow, Ui_MainWindow):
    def __init__(self):
        super().__init__()
        self.setupUi(self)
        self.limpiar_estado()

        # Conexiones de botones y menú
        self.btnAbrir.clicked.connect(self.abrir_archivo)
        self.actionAbrir.triggered.connect(self.abrir_archivo)
        self.btnPreprocesar.clicked.connect(self.preprocesar)
        self.btnMapas.clicked.connect(self.calcular_mapas)
        self.comboMapa.currentIndexChanged.connect(self.mostrar_mapa)
        self.btnSegmentar.clicked.connect(self.segmentar)
        self.btnMetricas.clicked.connect(self.calcular_metricas)
        self.btnExportar.clicked.connect(self.exportar_csv)
        self.actionExportar.triggered.connect(self.exportar_csv)
        self.actionSalir.triggered.connect(self.close)
        self.actionAcercaDe.triggered.connect(self.acerca_de)

        # Tablas: columnas que ocupan todo el ancho y sin numeración de filas
        for t in (self.tablaMetricas, self.tablaDescriptores):
            t.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
            t.verticalHeader().setVisible(False)

        # Lista de mapas: marcamos los elegidos en la etapa 3
        self.comboMapa.addItems([n + (" (seleccionada)" if n in SELECTED_FEATURES else "") for n in FEATURE_NAMES])

        # Índice del dataset para navegar por paciente y corte (si data/ existe)
        self.indice = build_index() if DATA_DIR.exists() else pd.DataFrame()
        if self.indice.empty:
            self.log("No se encontró data/: usá 'Abrir corte' para cargar un .tif.")
        else:
            self.log(f"Dataset: {self.indice['patient'].nunique()} pacientes, {len(self.indice)} cortes.")
        self.comboPaciente.currentIndexChanged.connect(self.llenar_cortes)
        self.chkSoloTumor.toggled.connect(self.llenar_pacientes)
        self.comboCorte.activated.connect(self.cargar_desde_combo)
        self.llenar_pacientes()
        self.actualizar_botones()

    # ---------- utilidades ----------
    def log(self, msg):
        """Agrega una línea al registro y a la barra de estado."""
        self.txtLog.appendPlainText(msg)
        self.statusbar.showMessage(msg, 5000)

    def limpiar_estado(self):
        """Borra todo lo calculado (se llama al cargar un corte nuevo)."""
        self.raw = self.gt = self.pre = self.brain = self.feats = None
        self.base = self.prop = self.metricas = self.descriptores = None

    def actualizar_botones(self):
        """Habilita cada paso solo si el anterior ya se hizo (respeta el orden del pipeline)."""
        self.btnPreprocesar.setEnabled(self.raw is not None)
        self.btnMapas.setEnabled(self.pre is not None)
        self.comboMapa.setEnabled(self.feats is not None)
        self.btnSegmentar.setEnabled(self.feats is not None)
        self.btnMetricas.setEnabled(self.prop is not None and self.gt is not None)
        hay_resultados = self.metricas is not None
        self.btnExportar.setEnabled(hay_resultados)
        self.actionExportar.setEnabled(hay_resultados)

    def ocupado(self, activo):
        """Cursor de espera mientras se calcula, para que se note que la ventana no está colgada."""
        if activo:
            QApplication.setOverrideCursor(Qt.WaitCursor)
            QApplication.processEvents()
        else:
            QApplication.restoreOverrideCursor()

    def dibujar(self, vista, paneles):
        """Dibuja en 'vista' una fila de paneles (titulo, imagen, cmap, [(mascara, color)]) con zoom vinculado."""
        vista.clear()
        cajas = []
        for col, (titulo, img, cmap, contornos) in enumerate(paneles):
            vista.addLabel(titulo, row=0, col=col)
            caja = vista.addViewBox(row=1, col=col, lockAspect=True, invertY=True)  # invertY: fila 0 arriba
            item = pg.ImageItem(img, levels=niveles(img))
            if cmap:
                item.setColorMap(pg.colormap.get(cmap))
            caja.addItem(item)
            for mask, color in contornos:
                if mask is not None and mask.any():
                    caja.addItem(pg.ImageItem(borde_rgba(mask, color)))
            if cajas:                                       # todos los paneles se mueven y hacen zoom juntos
                caja.setXLink(cajas[0])
                caja.setYLink(cajas[0])
            cajas.append(caja)

    # ---------- 1. Carga de datos ----------
    def llenar_pacientes(self):
        """Llena la lista de pacientes (opcionalmente solo los que tienen cortes con tumor)."""
        if self.indice.empty:
            return
        filas = self.indice[self.indice["has_tumor"]] if self.chkSoloTumor.isChecked() else self.indice
        self.comboPaciente.blockSignals(True)
        self.comboPaciente.clear()
        self.comboPaciente.addItems(sorted(filas["patient"].unique()))
        self.comboPaciente.blockSignals(False)
        self.llenar_cortes()

    def llenar_cortes(self):
        """Llena la lista de cortes del paciente elegido."""
        filas = self.indice[self.indice["patient"] == self.comboPaciente.currentText()]
        if self.chkSoloTumor.isChecked():
            filas = filas[filas["has_tumor"]]
        self.comboCorte.clear()
        for _, f in filas.iterrows():                       # guardamos la ruta como dato del ítem
            self.comboCorte.addItem(f"{f['slice']}  (tumor: {f['tumor_area']} px)", f["img_path"])

    def cargar_desde_combo(self):
        """Carga el corte elegido en la lista."""
        ruta = self.comboCorte.currentData()
        if ruta:
            self.cargar(Path(ruta))

    def abrir_archivo(self):
        """Diálogo para elegir un .tif; la máscara se busca al lado con el sufijo _mask."""
        ruta, _ = QFileDialog.getOpenFileName(self, "Abrir corte FLAIR", str(DATA_DIR), "Imágenes TIFF (*.tif)")
        if ruta:
            ruta = Path(ruta)
            if ruta.stem.endswith("_mask"):                 # si eligieron la máscara, cargamos su imagen
                ruta = ruta.with_name(ruta.stem[:-5] + ".tif")
            self.cargar(ruta)

    def cargar(self, ruta):
        """Lee el FLAIR y su máscara (si existe), resetea el estado y muestra la imagen original."""
        try:
            raw = load_flair(ruta)
        except Exception as e:
            QMessageBox.critical(self, "Error", f"No se pudo leer {ruta.name}:\n{e}")
            return
        self.limpiar_estado()
        self.raw = raw
        mask_path = ruta.with_name(f"{ruta.stem}_mask.tif")
        self.gt = load_mask(mask_path).astype(bool) if mask_path.exists() else None
        self.ruta = ruta
        self.lblArchivo.setText(ruta.name)
        self.dibujar(self.vistaOriginal, [("FLAIR original (rojo: máscara real)", self.raw, None, [(self.gt, ROJO)])])
        for v in (self.vistaPre, self.vistaMapa, self.vistaSegmentacion):
            v.clear()
        self.tablaMetricas.setRowCount(0)
        self.tablaDescriptores.setRowCount(0)
        self.tabsGraficos.setCurrentWidget(self.tabOriginal)
        self.barraProgreso.setValue(20)
        sin_gt = "" if self.gt is not None else " (sin máscara: no se podrán calcular métricas)"
        self.log(f"Cargado {ruta.name}{sin_gt}")
        self.actualizar_botones()

    # ---------- 2. Preprocesamiento ----------
    def preprocesar(self):
        """Máscara de cerebro, denoising y z-score (etapa 1)."""
        self.ocupado(True)
        self.brain = brain_mask(self.raw)
        self.pre = preprocess(self.raw)
        self.ocupado(False)
        self.dibujar(self.vistaPre, [("Máscara de cerebro", self.brain.astype(float), None, []),
                                     ("Preprocesada (NLM + z-score)", self.pre, None, [(self.gt, ROJO)])])
        self.tabsGraficos.setCurrentWidget(self.tabPre)
        self.barraProgreso.setValue(40)
        self.log(f"Preprocesado: cerebro = {100 * self.brain.mean():.1f} % de la imagen.")
        self.actualizar_botones()

    # ---------- 3. Mapas de características ----------
    def calcular_mapas(self):
        """Calcula los 12 mapas de la etapa 2 sobre la imagen preprocesada."""
        self.ocupado(True)
        self.feats = compute_features(self.pre)
        self.ocupado(False)
        self.tabsGraficos.setCurrentWidget(self.tabMapas)
        self.mostrar_mapa()
        self.barraProgreso.setValue(60)
        self.log(f"Mapas calculados: {self.feats.shape[-1]} ({len(SELECTED_FEATURES)} seleccionados en la etapa 3).")
        self.actualizar_botones()

    def mostrar_mapa(self):
        """Muestra el mapa elegido en la lista con el contorno de la máscara real."""
        if self.feats is None:
            return
        k = self.comboMapa.currentIndex()
        self.dibujar(self.vistaMapa, [(FEATURE_NAMES[k], self.feats[..., k], "viridis", [(self.gt, ROJO)])])

    # ---------- 4. Segmentación ----------
    def segmentar(self):
        """Línea base (Otsu) y método propuesto (k-means sobre las features elegidas), igual que en la etapa 5."""
        self.ocupado(True)
        self.base = postprocess(segment_baseline(self.raw))
        self.prop = postprocess(segment(self.feats[..., IDX_SEL], brain=self.brain, ref=self.feats[..., IDX_INT]))
        self.ocupado(False)
        self.dibujar(self.vistaSegmentacion, [
            ("Máscara real (GT)", self.raw, None, [(self.gt, ROJO)]),
            ("Línea base (Otsu)", self.raw, None, [(self.gt, ROJO), (self.base, AMARILLO)]),
            ("Propuesto (k-means)", self.raw, None, [(self.gt, ROJO), (self.prop, VERDE)]),
        ])
        self.tabsGraficos.setCurrentWidget(self.tabSegm)
        self.barraProgreso.setValue(80)
        self.log(f"Segmentado: Otsu = {self.base.sum()} px, k-means = {self.prop.sum()} px.")
        self.actualizar_botones()

    # ---------- 5. Resultados ----------
    def calcular_metricas(self):
        """Dice, IoU, sensibilidad y especificidad (etapa 5) y descriptores del tumor (etapa 6)."""
        self.metricas = {m: evaluate(p, self.gt) for m, p in (("Otsu", self.base), ("k-means", self.prop))}
        self.descriptores = {"GT": compute_descriptors(self.pre, self.gt),
                             "Predicha": compute_descriptors(self.pre, self.prop)}
        self.llenar_tabla(self.tablaMetricas, METRICAS, self.metricas["Otsu"], self.metricas["k-means"])
        self.llenar_tabla(self.tablaDescriptores, DESCRIPTORS, self.descriptores["GT"], self.descriptores["Predicha"])
        self.tabsGraficos.setCurrentWidget(self.tabMetricas)
        self.barraProgreso.setValue(100)
        self.log(f"Dice: Otsu = {self.metricas['Otsu']['Dice']:.3f} | k-means = {self.metricas['k-means']['Dice']:.3f}")
        self.actualizar_botones()

    @staticmethod
    def llenar_tabla(tabla, filas, col1, col2):
        """Escribe una fila por nombre con los valores de los dos diccionarios (3 decimales)."""
        tabla.setRowCount(len(filas))
        for i, nombre in enumerate(filas):
            for j, texto in enumerate((nombre, f"{col1[nombre]:.3f}", f"{col2[nombre]:.3f}")):
                tabla.setItem(i, j, QTableWidgetItem(texto))

    def exportar_csv(self):
        """Guarda métricas y descriptores del corte actual en un CSV (formato largo: una fila por valor)."""
        ruta, _ = QFileDialog.getSaveFileName(self, "Exportar CSV", f"results/interfaz_{self.ruta.stem}.csv", "CSV (*.csv)")
        if not ruta:
            return
        filas = [("metrica", k, metodo, v) for metodo, d in self.metricas.items() for k, v in d.items()]
        filas += [("descriptor", k, mascara, v) for mascara, d in self.descriptores.items() for k, v in d.items()]
        pd.DataFrame(filas, columns=["tipo", "nombre", "metodo", "valor"]).assign(corte=self.ruta.stem).to_csv(ruta, index=False)
        self.log(f"Exportado: {ruta}")

    def acerca_de(self):
        QMessageBox.about(self, "Acerca de",
                          "TPI PSIB 2026 - Grupo 14\nSegmentación de tumores en MRI FLAIR guiada por mapas de características.\n"
                          "Dimentstein, Grin, Pérez Raffo - ITBA")


if __name__ == "__main__":
    app = QApplication(sys.argv)
    ventana = MainWindow()
    ventana.show()
    sys.exit(app.exec())
