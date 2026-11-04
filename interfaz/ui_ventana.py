# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'ventana.ui'
##
## Created by: Qt User Interface Compiler version 6.12.0
##
## WARNING! All changes made in this file will be lost when recompiling UI file!
################################################################################

from PySide6.QtCore import (QCoreApplication, QDate, QDateTime, QLocale,
    QMetaObject, QObject, QPoint, QRect,
    QSize, QTime, QUrl, Qt)
from PySide6.QtGui import (QAction, QBrush, QColor, QConicalGradient,
    QCursor, QFont, QFontDatabase, QGradient,
    QIcon, QImage, QKeySequence, QLinearGradient,
    QPainter, QPalette, QPixmap, QRadialGradient,
    QTransform)
from PySide6.QtWidgets import (QAbstractItemView, QApplication, QCheckBox, QComboBox,
    QFormLayout, QGroupBox, QHBoxLayout, QHeaderView,
    QLabel, QMainWindow, QMenu, QMenuBar,
    QPlainTextEdit, QProgressBar, QPushButton, QSizePolicy,
    QSpacerItem, QStatusBar, QTabWidget, QTableWidget,
    QTableWidgetItem, QVBoxLayout, QWidget)

from pyqtgraph import GraphicsLayoutWidget

class Ui_MainWindow(object):
    def setupUi(self, MainWindow):
        if not MainWindow.objectName():
            MainWindow.setObjectName(u"MainWindow")
        MainWindow.resize(1300, 800)
        self.actionAbrir = QAction(MainWindow)
        self.actionAbrir.setObjectName(u"actionAbrir")
        self.actionExportar = QAction(MainWindow)
        self.actionExportar.setObjectName(u"actionExportar")
        self.actionSalir = QAction(MainWindow)
        self.actionSalir.setObjectName(u"actionSalir")
        self.actionAcercaDe = QAction(MainWindow)
        self.actionAcercaDe.setObjectName(u"actionAcercaDe")
        self.centralwidget = QWidget(MainWindow)
        self.centralwidget.setObjectName(u"centralwidget")
        self.layoutCentral = QVBoxLayout(self.centralwidget)
        self.layoutCentral.setObjectName(u"layoutCentral")
        self.layoutSuperior = QHBoxLayout()
        self.layoutSuperior.setObjectName(u"layoutSuperior")
        self.panelControles = QWidget(self.centralwidget)
        self.panelControles.setObjectName(u"panelControles")
        self.panelControles.setMaximumSize(QSize(320, 16777215))
        self.layoutPanel = QVBoxLayout(self.panelControles)
        self.layoutPanel.setObjectName(u"layoutPanel")
        self.layoutPanel.setContentsMargins(0, 0, 0, 0)
        self.grupoCarga = QGroupBox(self.panelControles)
        self.grupoCarga.setObjectName(u"grupoCarga")
        self.layout_grupoCarga = QFormLayout(self.grupoCarga)
        self.layout_grupoCarga.setObjectName(u"layout_grupoCarga")
        self.btnAbrir = QPushButton(self.grupoCarga)
        self.btnAbrir.setObjectName(u"btnAbrir")

        self.layout_grupoCarga.setWidget(0, QFormLayout.ItemRole.SpanningRole, self.btnAbrir)

        self.labelArchivo = QLabel(self.grupoCarga)
        self.labelArchivo.setObjectName(u"labelArchivo")

        self.layout_grupoCarga.setWidget(1, QFormLayout.ItemRole.LabelRole, self.labelArchivo)

        self.lblArchivo = QLabel(self.grupoCarga)
        self.lblArchivo.setObjectName(u"lblArchivo")
        self.lblArchivo.setWordWrap(True)

        self.layout_grupoCarga.setWidget(1, QFormLayout.ItemRole.FieldRole, self.lblArchivo)

        self.labelPaciente = QLabel(self.grupoCarga)
        self.labelPaciente.setObjectName(u"labelPaciente")

        self.layout_grupoCarga.setWidget(2, QFormLayout.ItemRole.LabelRole, self.labelPaciente)

        self.comboPaciente = QComboBox(self.grupoCarga)
        self.comboPaciente.setObjectName(u"comboPaciente")

        self.layout_grupoCarga.setWidget(2, QFormLayout.ItemRole.FieldRole, self.comboPaciente)

        self.labelCorte = QLabel(self.grupoCarga)
        self.labelCorte.setObjectName(u"labelCorte")

        self.layout_grupoCarga.setWidget(3, QFormLayout.ItemRole.LabelRole, self.labelCorte)

        self.comboCorte = QComboBox(self.grupoCarga)
        self.comboCorte.setObjectName(u"comboCorte")

        self.layout_grupoCarga.setWidget(3, QFormLayout.ItemRole.FieldRole, self.comboCorte)

        self.chkSoloTumor = QCheckBox(self.grupoCarga)
        self.chkSoloTumor.setObjectName(u"chkSoloTumor")
        self.chkSoloTumor.setChecked(True)

        self.layout_grupoCarga.setWidget(4, QFormLayout.ItemRole.SpanningRole, self.chkSoloTumor)


        self.layoutPanel.addWidget(self.grupoCarga)

        self.grupoPre = QGroupBox(self.panelControles)
        self.grupoPre.setObjectName(u"grupoPre")
        self.layout_grupoPre = QVBoxLayout(self.grupoPre)
        self.layout_grupoPre.setObjectName(u"layout_grupoPre")
        self.btnPreprocesar = QPushButton(self.grupoPre)
        self.btnPreprocesar.setObjectName(u"btnPreprocesar")

        self.layout_grupoPre.addWidget(self.btnPreprocesar)


        self.layoutPanel.addWidget(self.grupoPre)

        self.grupoMapas = QGroupBox(self.panelControles)
        self.grupoMapas.setObjectName(u"grupoMapas")
        self.layout_grupoMapas = QVBoxLayout(self.grupoMapas)
        self.layout_grupoMapas.setObjectName(u"layout_grupoMapas")
        self.btnMapas = QPushButton(self.grupoMapas)
        self.btnMapas.setObjectName(u"btnMapas")

        self.layout_grupoMapas.addWidget(self.btnMapas)

        self.labelMapa = QLabel(self.grupoMapas)
        self.labelMapa.setObjectName(u"labelMapa")

        self.layout_grupoMapas.addWidget(self.labelMapa)

        self.comboMapa = QComboBox(self.grupoMapas)
        self.comboMapa.setObjectName(u"comboMapa")

        self.layout_grupoMapas.addWidget(self.comboMapa)


        self.layoutPanel.addWidget(self.grupoMapas)

        self.grupoSegm = QGroupBox(self.panelControles)
        self.grupoSegm.setObjectName(u"grupoSegm")
        self.layout_grupoSegm = QVBoxLayout(self.grupoSegm)
        self.layout_grupoSegm.setObjectName(u"layout_grupoSegm")
        self.btnSegmentar = QPushButton(self.grupoSegm)
        self.btnSegmentar.setObjectName(u"btnSegmentar")

        self.layout_grupoSegm.addWidget(self.btnSegmentar)


        self.layoutPanel.addWidget(self.grupoSegm)

        self.grupoResultados = QGroupBox(self.panelControles)
        self.grupoResultados.setObjectName(u"grupoResultados")
        self.layout_grupoResultados = QVBoxLayout(self.grupoResultados)
        self.layout_grupoResultados.setObjectName(u"layout_grupoResultados")
        self.btnMetricas = QPushButton(self.grupoResultados)
        self.btnMetricas.setObjectName(u"btnMetricas")

        self.layout_grupoResultados.addWidget(self.btnMetricas)

        self.btnExportar = QPushButton(self.grupoResultados)
        self.btnExportar.setObjectName(u"btnExportar")

        self.layout_grupoResultados.addWidget(self.btnExportar)


        self.layoutPanel.addWidget(self.grupoResultados)

        self.spacerPanel = QSpacerItem(20, 40, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)

        self.layoutPanel.addItem(self.spacerPanel)


        self.layoutSuperior.addWidget(self.panelControles)

        self.tabsGraficos = QTabWidget(self.centralwidget)
        self.tabsGraficos.setObjectName(u"tabsGraficos")
        self.tabOriginal = QWidget()
        self.tabOriginal.setObjectName(u"tabOriginal")
        self.layout_tabOriginal = QVBoxLayout(self.tabOriginal)
        self.layout_tabOriginal.setObjectName(u"layout_tabOriginal")
        self.vistaOriginal = GraphicsLayoutWidget(self.tabOriginal)
        self.vistaOriginal.setObjectName(u"vistaOriginal")

        self.layout_tabOriginal.addWidget(self.vistaOriginal)

        self.tabsGraficos.addTab(self.tabOriginal, "")
        self.tabPre = QWidget()
        self.tabPre.setObjectName(u"tabPre")
        self.layout_tabPre = QVBoxLayout(self.tabPre)
        self.layout_tabPre.setObjectName(u"layout_tabPre")
        self.vistaPre = GraphicsLayoutWidget(self.tabPre)
        self.vistaPre.setObjectName(u"vistaPre")

        self.layout_tabPre.addWidget(self.vistaPre)

        self.tabsGraficos.addTab(self.tabPre, "")
        self.tabMapas = QWidget()
        self.tabMapas.setObjectName(u"tabMapas")
        self.layout_tabMapas = QVBoxLayout(self.tabMapas)
        self.layout_tabMapas.setObjectName(u"layout_tabMapas")
        self.vistaMapa = GraphicsLayoutWidget(self.tabMapas)
        self.vistaMapa.setObjectName(u"vistaMapa")

        self.layout_tabMapas.addWidget(self.vistaMapa)

        self.tabsGraficos.addTab(self.tabMapas, "")
        self.tabSegm = QWidget()
        self.tabSegm.setObjectName(u"tabSegm")
        self.layout_tabSegm = QVBoxLayout(self.tabSegm)
        self.layout_tabSegm.setObjectName(u"layout_tabSegm")
        self.vistaSegmentacion = GraphicsLayoutWidget(self.tabSegm)
        self.vistaSegmentacion.setObjectName(u"vistaSegmentacion")

        self.layout_tabSegm.addWidget(self.vistaSegmentacion)

        self.tabsGraficos.addTab(self.tabSegm, "")
        self.tabMetricas = QWidget()
        self.tabMetricas.setObjectName(u"tabMetricas")
        self.layout_tabMetricas = QVBoxLayout(self.tabMetricas)
        self.layout_tabMetricas.setObjectName(u"layout_tabMetricas")
        self.tablaMetricas = QTableWidget(self.tabMetricas)
        if (self.tablaMetricas.columnCount() < 4):
            self.tablaMetricas.setColumnCount(4)
        __qtablewidgetitem = QTableWidgetItem()
        self.tablaMetricas.setHorizontalHeaderItem(0, __qtablewidgetitem)
        __qtablewidgetitem1 = QTableWidgetItem()
        self.tablaMetricas.setHorizontalHeaderItem(1, __qtablewidgetitem1)
        __qtablewidgetitem2 = QTableWidgetItem()
        self.tablaMetricas.setHorizontalHeaderItem(2, __qtablewidgetitem2)
        __qtablewidgetitem3 = QTableWidgetItem()
        self.tablaMetricas.setHorizontalHeaderItem(3, __qtablewidgetitem3)
        self.tablaMetricas.setObjectName(u"tablaMetricas")
        self.tablaMetricas.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.tablaMetricas.horizontalHeader().setStretchLastSection(True)

        self.layout_tabMetricas.addWidget(self.tablaMetricas)

        self.tabsGraficos.addTab(self.tabMetricas, "")
        self.tabDescriptores = QWidget()
        self.tabDescriptores.setObjectName(u"tabDescriptores")
        self.layout_tabDescriptores = QVBoxLayout(self.tabDescriptores)
        self.layout_tabDescriptores.setObjectName(u"layout_tabDescriptores")
        self.tablaDescriptores = QTableWidget(self.tabDescriptores)
        if (self.tablaDescriptores.columnCount() < 3):
            self.tablaDescriptores.setColumnCount(3)
        __qtablewidgetitem4 = QTableWidgetItem()
        self.tablaDescriptores.setHorizontalHeaderItem(0, __qtablewidgetitem4)
        __qtablewidgetitem5 = QTableWidgetItem()
        self.tablaDescriptores.setHorizontalHeaderItem(1, __qtablewidgetitem5)
        __qtablewidgetitem6 = QTableWidgetItem()
        self.tablaDescriptores.setHorizontalHeaderItem(2, __qtablewidgetitem6)
        self.tablaDescriptores.setObjectName(u"tablaDescriptores")
        self.tablaDescriptores.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.tablaDescriptores.horizontalHeader().setStretchLastSection(True)

        self.layout_tabDescriptores.addWidget(self.tablaDescriptores)

        self.tabsGraficos.addTab(self.tabDescriptores, "")

        self.layoutSuperior.addWidget(self.tabsGraficos)


        self.layoutCentral.addLayout(self.layoutSuperior)

        self.txtLog = QPlainTextEdit(self.centralwidget)
        self.txtLog.setObjectName(u"txtLog")
        self.txtLog.setMaximumSize(QSize(16777215, 100))
        self.txtLog.setReadOnly(True)

        self.layoutCentral.addWidget(self.txtLog)

        self.barraProgreso = QProgressBar(self.centralwidget)
        self.barraProgreso.setObjectName(u"barraProgreso")
        self.barraProgreso.setValue(0)

        self.layoutCentral.addWidget(self.barraProgreso)

        MainWindow.setCentralWidget(self.centralwidget)
        self.menubar = QMenuBar(MainWindow)
        self.menubar.setObjectName(u"menubar")
        self.menubar.setGeometry(QRect(0, 0, 1300, 21))
        self.menuArchivo = QMenu(self.menubar)
        self.menuArchivo.setObjectName(u"menuArchivo")
        self.menuAyuda = QMenu(self.menubar)
        self.menuAyuda.setObjectName(u"menuAyuda")
        MainWindow.setMenuBar(self.menubar)
        self.statusbar = QStatusBar(MainWindow)
        self.statusbar.setObjectName(u"statusbar")
        MainWindow.setStatusBar(self.statusbar)

        self.menubar.addAction(self.menuArchivo.menuAction())
        self.menubar.addAction(self.menuAyuda.menuAction())
        self.menuArchivo.addAction(self.actionAbrir)
        self.menuArchivo.addAction(self.actionExportar)
        self.menuArchivo.addSeparator()
        self.menuArchivo.addAction(self.actionSalir)
        self.menuAyuda.addAction(self.actionAcercaDe)

        self.retranslateUi(MainWindow)

        self.tabsGraficos.setCurrentIndex(0)


        QMetaObject.connectSlotsByName(MainWindow)
    # setupUi

    def retranslateUi(self, MainWindow):
        MainWindow.setWindowTitle(QCoreApplication.translate("MainWindow", u"Segmentaci\u00f3n de tumores en MRI FLAIR", None))
        self.actionAbrir.setText(QCoreApplication.translate("MainWindow", u"Abrir...", None))
#if QT_CONFIG(shortcut)
        self.actionAbrir.setShortcut(QCoreApplication.translate("MainWindow", u"Ctrl+O", None))
#endif // QT_CONFIG(shortcut)
        self.actionExportar.setText(QCoreApplication.translate("MainWindow", u"Exportar CSV", None))
#if QT_CONFIG(shortcut)
        self.actionExportar.setShortcut(QCoreApplication.translate("MainWindow", u"Ctrl+E", None))
#endif // QT_CONFIG(shortcut)
        self.actionSalir.setText(QCoreApplication.translate("MainWindow", u"Salir", None))
#if QT_CONFIG(shortcut)
        self.actionSalir.setShortcut(QCoreApplication.translate("MainWindow", u"Ctrl+Q", None))
#endif // QT_CONFIG(shortcut)
        self.actionAcercaDe.setText(QCoreApplication.translate("MainWindow", u"Acerca de", None))
        self.grupoCarga.setTitle(QCoreApplication.translate("MainWindow", u"1. Carga de datos", None))
        self.btnAbrir.setText(QCoreApplication.translate("MainWindow", u"Abrir corte (.tif)...", None))
        self.labelArchivo.setText(QCoreApplication.translate("MainWindow", u"Archivo", None))
        self.lblArchivo.setText(QCoreApplication.translate("MainWindow", u"(ninguno)", None))
        self.labelPaciente.setText(QCoreApplication.translate("MainWindow", u"Paciente", None))
        self.labelCorte.setText(QCoreApplication.translate("MainWindow", u"Corte", None))
        self.chkSoloTumor.setText(QCoreApplication.translate("MainWindow", u"Solo cortes con tumor", None))
        self.grupoPre.setTitle(QCoreApplication.translate("MainWindow", u"2. Preprocesamiento", None))
        self.btnPreprocesar.setText(QCoreApplication.translate("MainWindow", u"Preprocesar", None))
        self.grupoMapas.setTitle(QCoreApplication.translate("MainWindow", u"3. Mapas de caracter\u00edsticas", None))
        self.btnMapas.setText(QCoreApplication.translate("MainWindow", u"Calcular mapas", None))
        self.labelMapa.setText(QCoreApplication.translate("MainWindow", u"Mapa a visualizar", None))
        self.grupoSegm.setTitle(QCoreApplication.translate("MainWindow", u"4. Segmentaci\u00f3n", None))
        self.btnSegmentar.setText(QCoreApplication.translate("MainWindow", u"Segmentar (Otsu, k-means y Chan-Vese)", None))
        self.grupoResultados.setTitle(QCoreApplication.translate("MainWindow", u"5. Resultados", None))
        self.btnMetricas.setText(QCoreApplication.translate("MainWindow", u"Calcular m\u00e9tricas", None))
        self.btnExportar.setText(QCoreApplication.translate("MainWindow", u"Exportar CSV", None))
        self.tabsGraficos.setTabText(self.tabsGraficos.indexOf(self.tabOriginal), QCoreApplication.translate("MainWindow", u"Original", None))
        self.tabsGraficos.setTabText(self.tabsGraficos.indexOf(self.tabPre), QCoreApplication.translate("MainWindow", u"Preprocesada", None))
        self.tabsGraficos.setTabText(self.tabsGraficos.indexOf(self.tabMapas), QCoreApplication.translate("MainWindow", u"Mapas", None))
        self.tabsGraficos.setTabText(self.tabsGraficos.indexOf(self.tabSegm), QCoreApplication.translate("MainWindow", u"Segmentaci\u00f3n", None))
        ___qtablewidgetitem = self.tablaMetricas.horizontalHeaderItem(0)
        ___qtablewidgetitem.setText(QCoreApplication.translate("MainWindow", u"M\u00e9trica", None))
        ___qtablewidgetitem1 = self.tablaMetricas.horizontalHeaderItem(1)
        ___qtablewidgetitem1.setText(QCoreApplication.translate("MainWindow", u"L\u00ednea base (Otsu)", None))
        ___qtablewidgetitem2 = self.tablaMetricas.horizontalHeaderItem(2)
        ___qtablewidgetitem2.setText(QCoreApplication.translate("MainWindow", u"k-means", None))
        ___qtablewidgetitem3 = self.tablaMetricas.horizontalHeaderItem(3)
        ___qtablewidgetitem3.setText(QCoreApplication.translate("MainWindow", u"k-means + Chan-Vese", None))
        self.tabsGraficos.setTabText(self.tabsGraficos.indexOf(self.tabMetricas), QCoreApplication.translate("MainWindow", u"M\u00e9tricas", None))
        ___qtablewidgetitem4 = self.tablaDescriptores.horizontalHeaderItem(0)
        ___qtablewidgetitem4.setText(QCoreApplication.translate("MainWindow", u"Descriptor", None))
        ___qtablewidgetitem5 = self.tablaDescriptores.horizontalHeaderItem(1)
        ___qtablewidgetitem5.setText(QCoreApplication.translate("MainWindow", u"M\u00e1scara real (GT)", None))
        ___qtablewidgetitem6 = self.tablaDescriptores.horizontalHeaderItem(2)
        ___qtablewidgetitem6.setText(QCoreApplication.translate("MainWindow", u"M\u00e1scara predicha", None))
        self.tabsGraficos.setTabText(self.tabsGraficos.indexOf(self.tabDescriptores), QCoreApplication.translate("MainWindow", u"Descriptores", None))
        self.txtLog.setPlaceholderText(QCoreApplication.translate("MainWindow", u"Registro de eventos...", None))
        self.menuArchivo.setTitle(QCoreApplication.translate("MainWindow", u"Archivo", None))
        self.menuAyuda.setTitle(QCoreApplication.translate("MainWindow", u"Ayuda", None))
    # retranslateUi

