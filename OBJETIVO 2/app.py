import sys
import os
import pandas as pd
from datetime import datetime
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                             QHBoxLayout, QTabWidget, QLabel, QMenuBar, QGroupBox,
                             QMessageBox, QFileDialog, QTableWidget, QTableWidgetItem,
                             QPushButton, QComboBox, QLineEdit, QHeaderView, QCheckBox,
                             QAbstractItemView, QDialog, QGridLayout, QFrame, QCompleter)
from PyQt6.QtCore import Qt, QDate
from PyQt6.QtGui import QFont, QAction, QColor

# 👇 IMPORTACIÓN DE TU CRONOGRAMA AVANZADO 👇
from visor_2 import VisorProjectPro

class SistemaContable(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("SISTEMA DE GESTIÓN - OBRA (PyQt6)")
        self.showMaximized()
        
        # --- GESTIÓN DE RUTAS ---
        self.carpeta_actual = os.getcwd() 
        self.nombre_obra = "General (Sin carpeta específica)"
        
        self.file_mat = "db_materiales.csv"
        self.file_mo = "db_mano_obra.csv"
        
        # Variables de memoria
        self.items_factura_actual = [] 
        self.lista_proveedores = []
        self.lista_insumos = []
        self.lista_trabajadores = []
        self.orden_por_fecha = False 

        # --- MENÚ SUPERIOR ---
        self.crear_menu()

        # --- CONTENEDOR PRINCIPAL ---
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.main_layout = QVBoxLayout(self.central_widget)

        # Encabezado
        self.lbl_titulo = QLabel(f"CONTROL DE COSTOS: {self.nombre_obra}")
        self.lbl_titulo.setFont(QFont("Segoe UI", 20, QFont.Weight.Bold))
        self.lbl_titulo.setStyleSheet("color: #2980b9;")
        self.main_layout.addWidget(self.lbl_titulo)

        # --- PESTAÑAS PRINCIPALES ---
        self.tabs = QTabWidget()
        self.tabs.setStyleSheet("QTabBar::tab { padding: 10px; font-weight: bold; }")
        self.main_layout.addWidget(self.tabs)

        self.tab_presupuesto = QWidget()
        self.tab_ejecucion   = QWidget()
        
        # Conexión directa con tu visor de Project
        self.tab_cronograma  = VisorProjectPro() 
        
        # Nueva pestaña EVM
        self.tab_evm = QWidget()

        self.tabs.addTab(self.tab_presupuesto, '  📊 PRESUPUESTO  ')
        self.tabs.addTab(self.tab_ejecucion,   '  💰 EJECUCIÓN (GASTOS)  ')
        self.tabs.addTab(self.tab_cronograma,  '  📅 CRONOGRAMA   ')
        self.tabs.addTab(self.tab_evm,         '  📈 CONTROL EVM (VALOR GANADO)  ')

        self.construir_presupuesto()
        self.construir_ejecucion_unificada()
        self.construir_modulo_evm()
        
        # Carga inicial
        self.recargar_todo()

    # ==================================================================
    # MENÚ Y GESTIÓN DE ARCHIVOS
    # ==================================================================
    def crear_menu(self):
        menubar = self.menuBar()
        file_menu = menubar.addMenu("📁 ARCHIVO / OBRAS")
        
        action_nueva = QAction("✨ Crear Nueva Obra", self)
        action_nueva.triggered.connect(self.nueva_obra)
        file_menu.addAction(action_nueva)
        
        action_abrir = QAction("📂 Abrir Obra Existente", self)
        action_abrir.triggered.connect(self.abrir_obra)
        file_menu.addAction(action_abrir)
        
        file_menu.addSeparator()
        action_salir = QAction("Salir", self)
        action_salir.triggered.connect(self.close)
        file_menu.addAction(action_salir)

    def nueva_obra(self):
        folder = QFileDialog.getExistingDirectory(self, "Selecciona una CARPETA VACÍA")
        if folder:
            self.carpeta_actual = folder
            self.nombre_obra = os.path.basename(folder).upper()
            pd.DataFrame(columns=["Numero_Factura","Fecha","Fecha_Uso","Proveedor","Insumo","Cantidad","Precio_Unit","Total"]).to_csv(os.path.join(self.carpeta_actual, self.file_mat), index=False)
            pd.DataFrame(columns=["Fecha","Trabajador","Cargo","Dias","Modo","Total","Observacion"]).to_csv(os.path.join(self.carpeta_actual, self.file_mo), index=False)
            self.actualizar_interfaz_obra()
            QMessageBox.information(self, "Éxito", f"Obra '{self.nombre_obra}' creada.")

    def abrir_obra(self):
        folder = QFileDialog.getExistingDirectory(self, "Selecciona la CARPETA de la obra")
        if folder:
            self.carpeta_actual = folder
            self.nombre_obra = os.path.basename(folder).upper()
            self.actualizar_interfaz_obra()

    def actualizar_interfaz_obra(self):
        self.setWindowTitle(f"SISTEMA DE GESTIÓN - OBRA: {self.nombre_obra}")
        self.lbl_titulo.setText(f"CONTROL DE COSTOS: {self.nombre_obra}")
        self.items_factura_actual = []
        self.tabla_temp.setRowCount(0)
        self.lbl_total_fact.setText("Total Factura: $ 0")
        self.recargar_todo()

    def recargar_todo(self):
        self.cargar_historial_mat()
        self.cargar_autocompletado_materiales()
        self.cargar_historial_mo()
        self.cargar_autocompletado_mo()
        self.actualizar_gran_total_obra()

    def ruta(self, archivo):
        return os.path.join(self.carpeta_actual, archivo)

    # ==================================================================
    # 1. PRESUPUESTO
    # ==================================================================
    def construir_presupuesto(self):
        layout = QVBoxLayout(self.tab_presupuesto)
        
        btn_cargar = QPushButton("📂 Cargar Excel de Presupuesto")
        btn_cargar.setStyleSheet("background-color: #27ae60; color: white; padding: 8px; font-weight: bold; border-radius: 4px;")
        btn_cargar.clicked.connect(self.cargar_apu)
        layout.addWidget(btn_cargar, alignment=Qt.AlignmentFlag.AlignLeft)
        
        self.tabla_apu = QTableWidget()
        self.tabla_apu.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.tabla_apu.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        layout.addWidget(self.tabla_apu)

    def cargar_apu(self):
        filename, _ = QFileDialog.getOpenFileName(self, "Abrir Excel", "", "Excel Files (*.xlsx *.xls)")
        if not filename: return
        try:
            df = pd.read_excel(filename, sheet_name="PRESUPUESTO", header=None).fillna("")
            self.tabla_apu.clear()
            self.tabla_apu.setColumnCount(len(df.columns))
            self.tabla_apu.setRowCount(len(df))
            
            headers = ["ITEM", "DESCRIPCIÓN", "UND", "CANT.", "VR. UNIT", "VR. TOTAL"]
            while len(headers) < len(df.columns):
                headers.append("-")
            
            self.tabla_apu.setHorizontalHeaderLabels(headers[:len(df.columns)])

            for i, row in df.iterrows():
                texto_fila = str(row.values).upper()
                es_titulo_o_subtotal = "SUBTOTAL" in texto_fila or "PRESUPUESTO DE OBRA" in texto_fila
                
                if len(row) > 2 and str(row[0]).strip() != "" and str(row[2]).strip() == "" and i > 5:
                    es_titulo_o_subtotal = True

                for j, val in enumerate(row):
                    texto = str(val)
                    if isinstance(val, (int, float)) and j in [4, 5] and val > 0 and i > 5:
                        texto = f"${val:,.0f}"

                    item = QTableWidgetItem(texto)
                    if es_titulo_o_subtotal:
                        item.setBackground(QColor("#d1ecf1"))
                        item.setForeground(QColor("#0c5460"))
                        font = QFont(); font.setBold(True); item.setFont(font)
                        
                    self.tabla_apu.setItem(i, j, item)
            
            self.tabla_apu.resizeColumnsToContents()
            if len(df.columns) > 1: self.tabla_apu.setColumnWidth(1, 450)
            
        except Exception as e: 
            QMessageBox.warning(self, "Aviso", f"No se pudo cargar el archivo Excel:\n{e}")

    # ==================================================================
    # 2. EJECUCIÓN (COMPRAS Y NÓMINA)
    # ==================================================================
    def construir_ejecucion_unificada(self):
        layout = QVBoxLayout(self.tab_ejecucion)
        
        self.lbl_costo_total_obra = QLabel("COSTO TOTAL EJECUTADO: $ 0")
        self.lbl_costo_total_obra.setFont(QFont("Segoe UI", 18, QFont.Weight.Bold))
        self.lbl_costo_total_obra.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lbl_costo_total_obra.setStyleSheet("background-color: #2c3e50; color: white; padding: 15px; border-radius: 5px;")
        layout.addWidget(self.lbl_costo_total_obra)

        self.notebook_gastos = QTabWidget()
        layout.addWidget(self.notebook_gastos)

        self.subtab_materiales = QWidget()
        self.subtab_mano_obra  = QWidget()

        self.notebook_gastos.addTab(self.subtab_materiales, ' 🧱 COMPRAS ')
        self.notebook_gastos.addTab(self.subtab_mano_obra,  ' 👷 NÓMINA ')

        self.construir_materiales_interno()
        self.construir_mo_interno()

    def construir_materiales_interno(self):
        layout = QHBoxLayout(self.subtab_materiales)
        
        panel_izq = QWidget(); l_izq = QVBoxLayout(panel_izq)
        layout.addWidget(panel_izq, stretch=1)

        grp_datos = QGroupBox("1. Datos Factura y Uso")
        l_datos = QGridLayout(grp_datos)
        self.var_fecha = QLineEdit(datetime.now().strftime("%d/%m/%Y"))
        self.var_num_factura = QLineEdit()
        self.var_proveedor = QComboBox(); self.var_proveedor.setEditable(True)

        # El botoncito Check para la fecha
        self.chk_misma_fecha = QCheckBox("Consumo Inmediato")
        self.chk_misma_fecha.setChecked(True)
        self.var_fecha_uso = QLineEdit(datetime.now().strftime("%d/%m/%Y"))
        self.var_fecha_uso.setEnabled(False) 

        self.chk_misma_fecha.toggled.connect(lambda est: [
        self.var_fecha_uso.setEnabled(not est),
        self.var_fecha_uso.setText(self.var_fecha.text()) if est else None
    ])

        l_datos.addWidget(QLabel("Fecha Factura:"), 0, 0); l_datos.addWidget(self.var_fecha, 0, 1)
        l_datos.addWidget(QLabel("N° Factura:"), 0, 2); l_datos.addWidget(self.var_num_factura, 0, 3)
        l_datos.addWidget(QLabel("Proveedor:"), 1, 0); l_datos.addWidget(self.var_proveedor, 1, 1, 1, 3)
        l_datos.addWidget(self.chk_misma_fecha, 2, 0, 1, 2)
        l_datos.addWidget(QLabel("Fecha Programada:"), 2, 2); l_datos.addWidget(self.var_fecha_uso, 2, 3)
        l_izq.addWidget(grp_datos)

        self.var_fecha = QLineEdit(datetime.now().strftime("%d/%m/%Y"))
        self.var_num_factura = QLineEdit()
        self.var_proveedor = QComboBox(); self.var_proveedor.setEditable(True)
        
        l_datos.addWidget(QLabel("Fecha:"), 0, 0); l_datos.addWidget(self.var_fecha, 0, 1)
        l_datos.addWidget(QLabel("N° Factura:"), 0, 2); l_datos.addWidget(self.var_num_factura, 0, 3)
        l_datos.addWidget(QLabel("Proveedor:"), 1, 0); l_datos.addWidget(self.var_proveedor, 1, 1, 1, 3)
        l_izq.addWidget(grp_datos)

        grp_add = QGroupBox("2. Agregar Ítems")
        l_add = QGridLayout(grp_add)
        self.var_insumo = QComboBox(); self.var_insumo.setEditable(True)
        self.var_cantidad = QLineEdit("1")
        self.var_precio = QLineEdit("0")
        self.var_iva = QCheckBox("Aplicar IVA (19%)")
        
        btn_agregar = QPushButton("⬇ AGREGAR")
        btn_agregar.setStyleSheet("background-color: #3498db; color: white; font-weight: bold;")
        btn_agregar.clicked.connect(self.agregar_item_lista)

        l_add.addWidget(QLabel("Insumo:"), 0, 0); l_add.addWidget(self.var_insumo, 0, 1, 1, 3)
        l_add.addWidget(QLabel("Cant:"), 1, 0); l_add.addWidget(self.var_cantidad, 1, 1)
        l_add.addWidget(QLabel("Vr. Unit:"), 1, 2); l_add.addWidget(self.var_precio, 1, 3)
        l_add.addWidget(self.var_iva, 2, 0, 1, 2); l_add.addWidget(btn_agregar, 2, 2, 1, 2)
        l_izq.addWidget(grp_add)

        grp_lista = QGroupBox("3. Detalle de Ítems")
        l_lista = QVBoxLayout(grp_lista)
        self.tabla_temp = QTableWidget(0, 4)
        self.tabla_temp.setHorizontalHeaderLabels(["Descripción", "Cant", "Unit", "Total"])
        self.tabla_temp.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        self.tabla_temp.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        l_lista.addWidget(self.tabla_temp)

        f_btns_temp = QHBoxLayout()
        btn_editar_temp = QPushButton("✏️ Editar"); btn_editar_temp.clicked.connect(self.editar_item_temporal)
        btn_quitar_temp = QPushButton("❌ Quitar"); btn_quitar_temp.clicked.connect(self.eliminar_item_temporal)
        f_btns_temp.addWidget(btn_editar_temp); f_btns_temp.addWidget(btn_quitar_temp)
        l_lista.addLayout(f_btns_temp)
        l_izq.addWidget(grp_lista)

        self.lbl_total_fact = QLabel("Total Factura: $ 0")
        self.lbl_total_fact.setFont(QFont("Segoe UI", 14, QFont.Weight.Bold))
        self.lbl_total_fact.setAlignment(Qt.AlignmentFlag.AlignRight)
        btn_guardar = QPushButton("💾 TERMINAR Y GUARDAR FACTURA")
        btn_guardar.setStyleSheet("background-color: #27ae60; color: white; padding: 10px; font-weight: bold;")
        btn_guardar.clicked.connect(self.guardar_factura_completa)
        l_izq.addWidget(self.lbl_total_fact)
        l_izq.addWidget(btn_guardar)

        panel_der = QGroupBox("Historial de Compras")
        l_der = QVBoxLayout(panel_der)
        layout.addWidget(panel_der, stretch=2)

        f_busqueda = QHBoxLayout()
        self.var_buscar_mat = QLineEdit()
        btn_buscar = QPushButton("🔍 Buscar"); btn_buscar.clicked.connect(self.filtrar_historial_mat)
        self.btn_orden = QPushButton("🔃 Ordenar: Creación"); self.btn_orden.clicked.connect(self.alternar_orden_historial)
        btn_edit_hist = QPushButton("✏️ Editar Datos"); btn_edit_hist.clicked.connect(lambda: self.ver_detalle_factura(modo_edicion=True))
        btn_del_hist = QPushButton("🗑 Eliminar"); btn_del_hist.setStyleSheet("color: red;"); btn_del_hist.clicked.connect(self.eliminar_factura)
        
        f_busqueda.addWidget(self.var_buscar_mat); f_busqueda.addWidget(btn_buscar); f_busqueda.addWidget(self.btn_orden)
        f_busqueda.addWidget(btn_edit_hist); f_busqueda.addWidget(btn_del_hist)
        l_der.addLayout(f_busqueda)

        self.lbl_total_mat = QLabel("Acumulado: $ 0")
        self.lbl_total_mat.setFont(QFont("Segoe UI", 11, QFont.Weight.Bold))
        self.lbl_total_mat.setAlignment(Qt.AlignmentFlag.AlignRight)
        l_der.addWidget(self.lbl_total_mat)

        self.tabla_hist_mat = QTableWidget(0, 5)
        self.tabla_hist_mat.setHorizontalHeaderLabels(["Fecha", "Fact", "Prov", "Item", "Total"])
        self.tabla_hist_mat.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeMode.Stretch)
        self.tabla_hist_mat.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.tabla_hist_mat.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.tabla_hist_mat.itemDoubleClicked.connect(lambda e: self.ver_detalle_factura(modo_edicion=False))
        l_der.addWidget(self.tabla_hist_mat)

    def construir_mo_interno(self):
        layout = QHBoxLayout(self.subtab_mano_obra)
        
        panel_izq = QGroupBox("Registrar Pago"); panel_izq.setStyleSheet("QGroupBox { font-weight: bold; }")
        l_izq = QVBoxLayout(panel_izq); layout.addWidget(panel_izq, stretch=1)
        
        f_trab = QGridLayout()
        self.mo_fecha = QLineEdit(datetime.now().strftime("%d/%m/%Y"))
        self.mo_trabajador = QComboBox(); self.mo_trabajador.setEditable(True)
        self.mo_cargo = QComboBox(); self.mo_cargo.addItems(["OFICIAL", "AYUDANTE", "MAESTRO", "CONTRATISTA"])
        self.mo_modo_pago = QComboBox(); self.mo_modo_pago.addItems(["POR DÍA (JORNAL)", "PRECIO GLOBAL / MENSUAL"])
        self.mo_modo_pago.currentIndexChanged.connect(self.cambiar_modo_pago)
        
        self.lbl_dias = QLabel("Días Trab.:"); self.mo_dias = QLineEdit("1")
        self.lbl_valor = QLabel("Valor Día:"); self.mo_valor = QLineEdit("0")
        self.mo_observacion = QLineEdit()

        f_trab.addWidget(QLabel("Trabajador:"), 0, 0); f_trab.addWidget(self.mo_trabajador, 0, 1, 1, 3)
        f_trab.addWidget(QLabel("Cargo:"), 1, 0); f_trab.addWidget(self.mo_cargo, 1, 1)
        f_trab.addWidget(QLabel("Modalidad:"), 2, 0); f_trab.addWidget(self.mo_modo_pago, 2, 1, 1, 3)
        f_trab.addWidget(QLabel("Fecha:"), 3, 0); f_trab.addWidget(self.mo_fecha, 3, 1)
        f_trab.addWidget(self.lbl_dias, 4, 0); f_trab.addWidget(self.mo_dias, 4, 1)
        f_trab.addWidget(self.lbl_valor, 4, 2); f_trab.addWidget(self.mo_valor, 4, 3)
        f_trab.addWidget(QLabel("Observación:"), 5, 0); f_trab.addWidget(self.mo_observacion, 5, 1, 1, 3)
        
        btn_mo = QPushButton("REGISTRAR PAGO")
        btn_mo.setStyleSheet("background-color: #f39c12; color: white; padding: 10px; font-weight: bold;")
        btn_mo.clicked.connect(self.guardar_mo)

        l_izq.addLayout(f_trab); l_izq.addStretch(); l_izq.addWidget(btn_mo)

        panel_der = QGroupBox("Historial de Pagos")
        l_der = QVBoxLayout(panel_der); layout.addWidget(panel_der, stretch=2)

        self.lbl_total_mo = QLabel("Acumulado Nómina: $ 0")
        self.lbl_total_mo.setFont(QFont("Segoe UI", 11, QFont.Weight.Bold))
        self.lbl_total_mo.setAlignment(Qt.AlignmentFlag.AlignRight)
        l_der.addWidget(self.lbl_total_mo)

        self.tabla_hist_mo = QTableWidget(0, 5)
        self.tabla_hist_mo.setHorizontalHeaderLabels(["Fecha", "Nombre", "Modo", "Observación", "Pagado"])
        self.tabla_hist_mo.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self.tabla_hist_mo.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.tabla_hist_mo.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        l_der.addWidget(self.tabla_hist_mo)

    def cambiar_modo_pago(self):
        if self.mo_modo_pago.currentText() == "POR DÍA (JORNAL)":
            self.mo_dias.setEnabled(True)
            self.lbl_dias.setText("Días Trab.:")
            self.lbl_valor.setText("Valor Día:")
        else:
            self.mo_dias.setText("1")
            self.mo_dias.setEnabled(False)
            self.lbl_dias.setText("Días (Fijo):")
            self.lbl_valor.setText("Valor Total:")

    def configurar_autocompletado(self, combo, lista):
        completer = QCompleter(lista)
        completer.setCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)
        completer.setFilterMode(Qt.MatchFlag.MatchContains)
        combo.setCompleter(completer)

    def agregar_item_lista(self):
        insumo = self.var_insumo.currentText().upper()
        if not insumo: return
        try:
            cantidad = float(self.var_cantidad.text())
            precio_unit = float(self.var_precio.text())
        except ValueError:
            QMessageBox.warning(self, "Error", "Cantidad y precio deben ser numéricos.")
            return

        subtotal = cantidad * precio_unit
        if self.var_iva.isChecked():
            total = subtotal * 1.19
            insumo += " (c/IVA)"
        else:
            total = subtotal

        item = {"Insumo": insumo, "Cantidad": cantidad, "Precio": precio_unit, "Total": total}
        self.items_factura_actual.append(item)
        
        row = self.tabla_temp.rowCount()
        self.tabla_temp.insertRow(row)
        self.tabla_temp.setItem(row, 0, QTableWidgetItem(insumo))
        self.tabla_temp.setItem(row, 1, QTableWidgetItem(str(cantidad)))
        self.tabla_temp.setItem(row, 2, QTableWidgetItem(f"${precio_unit:,.0f}"))
        self.tabla_temp.setItem(row, 3, QTableWidgetItem(f"${total:,.0f}"))
        
        self.lbl_total_fact.setText(f"Total Factura: ${sum(x['Total'] for x in self.items_factura_actual):,.0f}")
        self.var_insumo.setCurrentText("")
        self.var_precio.setText("0")
        self.var_cantidad.setText("1") 

    def eliminar_item_temporal(self):
        row = self.tabla_temp.currentRow()
        if row < 0: return
        del self.items_factura_actual[row]
        self.tabla_temp.removeRow(row)
        self.lbl_total_fact.setText(f"Total Factura: ${sum(x['Total'] for x in self.items_factura_actual):,.0f}")

    def editar_item_temporal(self):
        row = self.tabla_temp.currentRow()
        if row < 0: return
        item = self.items_factura_actual[row]
        
        nombre_raw = item["Insumo"]
        if "(C/IVA)" in nombre_raw.upper():
            self.var_iva.setChecked(True)
            self.var_insumo.setCurrentText(nombre_raw.replace(" (c/IVA)", "").replace(" (C/IVA)", ""))
        else:
            self.var_iva.setChecked(False)
            self.var_insumo.setCurrentText(nombre_raw)
            
        self.var_cantidad.setText(str(item["Cantidad"]))
        self.var_precio.setText(str(item["Precio"]))
        
        del self.items_factura_actual[row]
        self.tabla_temp.removeRow(row)
        self.lbl_total_fact.setText(f"Total Factura: ${sum(x['Total'] for x in self.items_factura_actual):,.0f}")

    def guardar_factura_completa(self):
        if not self.items_factura_actual or not self.var_num_factura.text():
            QMessageBox.warning(self, "Error", "Faltan datos de factura o ítems.")
            return
            
        datos = []
        for i in self.items_factura_actual:
            datos.append({
                "Numero_Factura": self.var_num_factura.text().upper(), 
                "Fecha": self.var_fecha.text(), 
                "Fecha_Uso": self.var_fecha.text() if self.chk_misma_fecha.isChecked() else self.var_fecha_uso.text(),
                "Proveedor": self.var_proveedor.currentText().upper(), 
                "Insumo": i["Insumo"], 
                "Cantidad": i["Cantidad"], 
                "Precio_Unit": i["Precio"], 
                "Total": i["Total"]
            })
        df = pd.DataFrame(datos)
        ruta_archivo = self.ruta(self.file_mat)
        h = not os.path.isfile(ruta_archivo)
        df.to_csv(ruta_archivo, mode='a', header=h, index=False)
        
        self.items_factura_actual = []
        self.tabla_temp.setRowCount(0)
        self.var_num_factura.setText(""); self.var_proveedor.setCurrentText("") 
        self.lbl_total_fact.setText("Total Factura: $ 0")
        self.recargar_todo()
        QMessageBox.information(self, "Guardado", "Factura guardada correctamente.")

    def alternar_orden_historial(self):
        self.orden_por_fecha = not self.orden_por_fecha
        self.btn_orden.setText("🔃 Ordenar: Fecha (Reciente)" if self.orden_por_fecha else "🔃 Ordenar: Creación")
        self.cargar_historial_mat()

    def cargar_historial_mat(self):
        self.tabla_hist_mat.setRowCount(0)
        ruta_archivo = self.ruta(self.file_mat)
        if os.path.isfile(ruta_archivo):
            try:
                df = pd.read_csv(ruta_archivo).fillna("")
                if self.orden_por_fecha:
                    df['Fecha_DT'] = pd.to_datetime(df['Fecha'], dayfirst=True, errors='coerce')
                    df = df.sort_values(by='Fecha_DT', ascending=False)
                
                t = 0
                for i, r in df.iterrows():
                    row_idx = self.tabla_hist_mat.rowCount()
                    self.tabla_hist_mat.insertRow(row_idx)
                    
                    factura_vis = str(r["Numero_Factura"]).replace(".0", "")
                    it_fecha = QTableWidgetItem(str(r["Fecha"]))
                    it_fecha.setData(Qt.ItemDataRole.UserRole, i) 
                    
                    self.tabla_hist_mat.setItem(row_idx, 0, it_fecha)
                    self.tabla_hist_mat.setItem(row_idx, 1, QTableWidgetItem(factura_vis))
                    self.tabla_hist_mat.setItem(row_idx, 2, QTableWidgetItem(str(r["Proveedor"])))
                    self.tabla_hist_mat.setItem(row_idx, 3, QTableWidgetItem(str(r["Insumo"])))
                    self.tabla_hist_mat.setItem(row_idx, 4, QTableWidgetItem(f"${float(r['Total']):,.0f}"))

                    if "Fecha_Uso" in df.columns and str(r["Fecha"]) != str(r["Fecha_Uso"]):
                        for c in range(5): self.tabla_hist_mat.item(row_idx, c).setBackground(QColor("#fcf3cf"))

                    t += float(r["Total"])
                    
                self.lbl_total_mat.setText(f"Acumulado: $ {t:,.0f}")
                return t
            except Exception as e: print(e); return 0
        return 0

    def filtrar_historial_mat(self):
        q = self.var_buscar_mat.text().upper()
        self.tabla_hist_mat.setRowCount(0)
        ruta_archivo = self.ruta(self.file_mat)
        if os.path.isfile(ruta_archivo):
            try:
                df = pd.read_csv(ruta_archivo).fillna("")
                mask = df.astype(str).apply(lambda x: x.str.contains(q, case=False)).any(axis=1)
                df_filtrado = df[mask]
                
                for i, r in df_filtrado.iterrows():
                    row_idx = self.tabla_hist_mat.rowCount()
                    self.tabla_hist_mat.insertRow(row_idx)
                    factura_vis = str(r["Numero_Factura"]).replace(".0", "")
                    it_fecha = QTableWidgetItem(str(r["Fecha"]))
                    it_fecha.setData(Qt.ItemDataRole.UserRole, i) 
                    
                    self.tabla_hist_mat.setItem(row_idx, 0, it_fecha)
                    self.tabla_hist_mat.setItem(row_idx, 1, QTableWidgetItem(factura_vis))
                    self.tabla_hist_mat.setItem(row_idx, 2, QTableWidgetItem(str(r["Proveedor"])))
                    self.tabla_hist_mat.setItem(row_idx, 3, QTableWidgetItem(str(r["Insumo"])))
                    self.tabla_hist_mat.setItem(row_idx, 4, QTableWidgetItem(f"${float(r['Total']):,.0f}"))

                    if "Fecha_Uso" in df.columns and str(r["Fecha"]) != str(r["Fecha_Uso"]):
                        for c in range(5): self.tabla_hist_mat.item(row_idx, c).setBackground(QColor("#fcf3cf"))
            except: pass

    def eliminar_factura(self):
        row = self.tabla_hist_mat.currentRow()
        if row < 0: 
            QMessageBox.warning(self, "Aviso", "Selecciona la fila que quieres eliminar.")
            return
            
        num_orig = self.tabla_hist_mat.item(row, 1).text().strip()
        prov_orig = self.tabla_hist_mat.item(row, 2).text().strip()

        rep = QMessageBox.question(self, "Confirmar", f"¿Eliminar TODAS las líneas de:\nFactura: {num_orig}\nProveedor: {prov_orig}?")
        if rep != QMessageBox.StandardButton.Yes: return

        ruta_archivo = self.ruta(self.file_mat)
        try:
            df = pd.read_csv(ruta_archivo).fillna("")
            df['TEMP_FACTURA'] = df['Numero_Factura'].astype(str).str.replace(r'\.0$', '', regex=True).str.strip().str.upper()
            df['TEMP_PROVEEDOR'] = df['Proveedor'].astype(str).str.strip().str.upper()
            mask_borrar = (df['TEMP_FACTURA'] == num_orig.upper()) & (df['TEMP_PROVEEDOR'] == prov_orig.upper())
            
            if not mask_borrar.any():
                QMessageBox.warning(self, "Error", "No se encontró coincidencia.")
                return

            df_final = df[~mask_borrar].copy()
            df_final = df_final.drop(columns=['TEMP_FACTURA', 'TEMP_PROVEEDOR'])
            df_final.to_csv(ruta_archivo, index=False)
            
            self.recargar_todo()
            QMessageBox.information(self, "Éxito", "Factura eliminada correctamente.")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"No se pudo eliminar: {e}")

    def cargar_autocompletado_materiales(self):
        ruta_archivo = self.ruta(self.file_mat)
        if os.path.isfile(ruta_archivo):
            try:
                df = pd.read_csv(ruta_archivo).fillna("")
                self.lista_proveedores = sorted(df["Proveedor"].astype(str).unique().tolist())
                self.var_proveedor.clear(); self.var_proveedor.addItems(self.lista_proveedores)
                self.configurar_autocompletado(self.var_proveedor, self.lista_proveedores)
                
                self.lista_insumos = sorted(df["Insumo"].astype(str).unique().tolist())
                self.var_insumo.clear(); self.var_insumo.addItems(self.lista_insumos)
                self.configurar_autocompletado(self.var_insumo, self.lista_insumos)
            except: pass

    def ver_detalle_factura(self, modo_edicion=False):
        row = self.tabla_hist_mat.currentRow()
        if row < 0: return
        
        num_orig = self.tabla_hist_mat.item(row, 1).text().strip()
        prov_orig = self.tabla_hist_mat.item(row, 2).text().strip()
        ruta_archivo = self.ruta(self.file_mat)
        if not os.path.isfile(ruta_archivo): return

        df = pd.read_csv(ruta_archivo).fillna("")
        df['TEMP_FACTURA'] = df['Numero_Factura'].astype(str).str.replace(r'\.0$', '', regex=True).str.strip().str.upper()
        df['TEMP_PROVEEDOR'] = df['Proveedor'].astype(str).str.strip().str.upper()
        mask = (df['TEMP_FACTURA'] == num_orig.upper()) & (df['TEMP_PROVEEDOR'] == prov_orig.upper())
        items = df[mask]
        
        if items.empty: return
        fecha_val = items.iloc[0]["Fecha"]
        fecha_uso_val = items.iloc[0].get("Fecha_Uso", fecha_val)

        dialog = QDialog(self)
        dialog.setWindowTitle(f"EDITAR DATOS FACTURA {num_orig}" if modo_edicion else f"Detalle de Factura N° {num_orig}")
        dialog.resize(900, 600)
        d_layout = QVBoxLayout(dialog)
        
        f_header = QFrame(); d_layout.addWidget(f_header)
        hl = QGridLayout(f_header)
        
        if modo_edicion:
            hl.addWidget(QLabel("N° FACTURA:"), 0, 0)
            ent_num = QLineEdit(num_orig); hl.addWidget(ent_num, 0, 1)
            hl.addWidget(QLabel("FECHA:"), 0, 2)
            ent_fecha = QLineEdit(fecha_val); hl.addWidget(ent_fecha, 0, 3)
            

            hl.addWidget(QLabel("PROVEEDOR:"), 1, 0)
            ent_prov = QLineEdit(prov_orig); hl.addWidget(ent_prov, 1, 1)
            hl.addWidget(QLabel("Fecha Programada"), 1, 2)
            ent_fecha_uso = QLineEdit(str(fecha_uso_val)); hl.addWidget(ent_fecha_uso, 1, 3)

            def guardar_cambios():
                nuevo_num = ent_num.text().upper().strip()
                nueva_fecha = ent_fecha.text().strip()
                nueva_fecha_uso = ent_fecha_uso.text().strip()
                nuevo_prov = ent_prov.text().upper().strip()

                if not nuevo_num or not nuevo_prov: return
                
                df_edit = pd.read_csv(ruta_archivo).fillna("")
                df_edit['TEMP_FACTURA'] = df_edit['Numero_Factura'].astype(str).str.replace(r'\.0$', '', regex=True).str.strip().str.upper()
                df_edit['TEMP_PROVEEDOR'] = df_edit['Proveedor'].astype(str).str.strip().str.upper()
                mask_edit = (df_edit['TEMP_FACTURA'] == num_orig.upper()) & (df_edit['TEMP_PROVEEDOR'] == prov_orig.upper())
                
                df_edit.loc[mask_edit, 'Numero_Factura'] = nuevo_num
                df_edit.loc[mask_edit, 'Fecha'] = nueva_fecha
                df_edit.loc[mask_edit, 'Proveedor'] = nuevo_prov
                df_edit = df_edit.drop(columns=['TEMP_FACTURA', 'TEMP_PROVEEDOR'])
                df_edit.to_csv(ruta_archivo, index=False)
                
                self.recargar_todo(); dialog.accept()
                QMessageBox.information(self, "Éxito", "Datos actualizados.")

            btn_save = QPushButton("💾 GUARDAR CAMBIOS")
            btn_save.setStyleSheet("background-color: #27ae60; color: white;")
            btn_save.clicked.connect(guardar_cambios)
            hl.addWidget(btn_save, 2, 3)
        else:
            lbl_title = QLabel(f"FACTURA N° {num_orig}")
            lbl_title.setFont(QFont("Segoe UI", 20, QFont.Weight.Bold))
            hl.addWidget(lbl_title, 0, 0, 3, 1)
            
            hl.addWidget(QLabel(f"<b>FECHA COMPRA:</b> {fecha_val}"), 0, 1, alignment=Qt.AlignmentFlag.AlignRight)

            lbl_prog = QLabel(f"<b>FECHA PROGRAMADA:</b> {fecha_uso_val}")
            if fecha_val != fecha_uso_val: 
                lbl_prog.setStyleSheet("color: #d35400; font-weight: bold;")
            hl.addWidget(lbl_prog, 1, 1, alignment=Qt.AlignmentFlag.AlignRight)

            hl.addWidget(QLabel(f"<b>PROVEEDOR:</b> {prov_orig}"), 2, 1, alignment=Qt.AlignmentFlag.AlignRight)

        tabla_diag = QTableWidget(0, 6)
        tabla_diag.setHorizontalHeaderLabels(["Insumo", "Cant", "Vr. Unit", "IVA", "Subtotal", "Total Neto"])
        tabla_diag.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        tabla_diag.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        d_layout.addWidget(tabla_diag)

        sum_subtotal = 0; sum_iva = 0; sum_total = 0
        for _, r in items.iterrows():
            nombre_raw = str(r["Insumo"]); cantidad = float(r["Cantidad"]); total_linea = float(r["Total"])
            if "(C/IVA)" in nombre_raw.upper():
                nombre_clean = nombre_raw.upper().replace("(C/IVA)", "").strip()
                base = total_linea / 1.19; iva = total_linea - base; txt_iva = "19%"
            else:
                nombre_clean = nombre_raw; base = total_linea; iva = 0; txt_iva = "0%"
            precio_unit = float(r["Precio_Unit"])

            r_idx = tabla_diag.rowCount()
            tabla_diag.insertRow(r_idx)
            tabla_diag.setItem(r_idx, 0, QTableWidgetItem(nombre_clean))
            tabla_diag.setItem(r_idx, 1, QTableWidgetItem(str(cantidad)))
            tabla_diag.setItem(r_idx, 2, QTableWidgetItem(f"${precio_unit:,.0f}"))
            tabla_diag.setItem(r_idx, 3, QTableWidgetItem(txt_iva))
            tabla_diag.setItem(r_idx, 4, QTableWidgetItem(f"${base:,.0f}"))
            tabla_diag.setItem(r_idx, 5, QTableWidgetItem(f"${total_linea:,.0f}"))
            sum_subtotal += base; sum_iva += iva; sum_total += total_linea

        f_tot = QFrame(); d_layout.addWidget(f_tot)
        tl = QGridLayout(f_tot)
        tl.addWidget(QLabel("SUBTOTAL:"), 0, 0, alignment=Qt.AlignmentFlag.AlignRight)
        tl.addWidget(QLabel(f"${sum_subtotal:,.0f}"), 0, 1)
        tl.addWidget(QLabel("IVA (19%):"), 1, 0, alignment=Qt.AlignmentFlag.AlignRight)
        tl.addWidget(QLabel(f"${sum_iva:,.0f}"), 1, 1)
        lbl_gran = QLabel(f"TOTAL A PAGAR:")
        lbl_gran.setFont(QFont("Segoe UI", 14, QFont.Weight.Bold))
        tl.addWidget(lbl_gran, 2, 0, alignment=Qt.AlignmentFlag.AlignRight)
        lbl_val = QLabel(f"${sum_total:,.0f}")
        lbl_val.setFont(QFont("Segoe UI", 14, QFont.Weight.Bold))
        lbl_val.setStyleSheet("color: #27ae60;")
        tl.addWidget(lbl_val, 2, 1)
        dialog.exec()

    def guardar_mo(self):
        trab = self.mo_trabajador.currentText().upper()
        try: valor = float(self.mo_valor.text())
        except: return
        if not trab or valor == 0: return
        
        try: dias = float(self.mo_dias.text())
        except: dias = 1.0

        if self.mo_modo_pago.currentText() == "POR DÍA (JORNAL)":
            total = dias * valor; modo_txt = "Jornal"
        else: total = valor; dias = 1; modo_txt = "Global"
        
        obs = self.mo_observacion.text().upper()
        n = {"Fecha": self.mo_fecha.text(), "Trabajador": trab, "Cargo": self.mo_cargo.currentText().upper(), 
             "Dias": dias, "Modo": modo_txt, "Total": total, "Observacion": obs}
             
        df = pd.DataFrame([n])
        ruta_archivo = self.ruta(self.file_mo)
        h = not os.path.isfile(ruta_archivo)
        df.to_csv(ruta_archivo, mode='a', header=h, index=False)
        
        if self.mo_modo_pago.currentText() == "POR DÍA (JORNAL)": self.mo_dias.setText("1.0")
        self.mo_trabajador.setCurrentText(""); self.mo_valor.setText("0"); self.mo_observacion.setText("")
        self.recargar_todo()
        QMessageBox.information(self, "Guardado", "Pago registrado.")

    def cargar_historial_mo(self):
        self.tabla_hist_mo.setRowCount(0)
        ruta_archivo = self.ruta(self.file_mo)
        if os.path.isfile(ruta_archivo):
            try:
                df = pd.read_csv(ruta_archivo)
                if "Observacion" not in df.columns: df["Observacion"] = ""
                df = df.fillna("") 
                t = 0
                for _, r in df.iterrows():
                    row_idx = self.tabla_hist_mo.rowCount()
                    self.tabla_hist_mo.insertRow(row_idx)
                    self.tabla_hist_mo.setItem(row_idx, 0, QTableWidgetItem(str(r["Fecha"])))
                    self.tabla_hist_mo.setItem(row_idx, 1, QTableWidgetItem(str(r["Trabajador"])))
                    self.tabla_hist_mo.setItem(row_idx, 2, QTableWidgetItem(str(r["Modo"])))
                    self.tabla_hist_mo.setItem(row_idx, 3, QTableWidgetItem(str(r["Observacion"])))
                    self.tabla_hist_mo.setItem(row_idx, 4, QTableWidgetItem(f"${float(r['Total']):,.0f}"))
                    t += float(r["Total"])
                self.lbl_total_mo.setText(f"Acumulado Nómina: $ {t:,.0f}")
                return t
            except: return 0
        return 0

    def cargar_autocompletado_mo(self):
        ruta_archivo = self.ruta(self.file_mo)
        if os.path.isfile(ruta_archivo):
            try:
                df = pd.read_csv(ruta_archivo)
                self.lista_trabajadores = sorted(df["Trabajador"].astype(str).str.upper().unique().tolist())
                self.mo_trabajador.clear(); self.mo_trabajador.addItems(self.lista_trabajadores)
                self.configurar_autocompletado(self.mo_trabajador, self.lista_trabajadores)
            except: pass

    def actualizar_gran_total_obra(self):
        t_mat = self.cargar_historial_mat()
        t_mo = self.cargar_historial_mo()
        gran_total = t_mat + t_mo
        self.lbl_costo_total_obra.setText(f"COSTO TOTAL EJECUTADO ({self.nombre_obra}): $ {gran_total:,.0f}")

    # ==================================================================
    # 3. MÓDULO EVM (VALOR GANADO) - CONECTADO AL CORTE DE OBRA
    # ==================================================================
    def construir_modulo_evm(self):
        layout_principal = QVBoxLayout(self.tab_evm)
        
        # 1. Panel Superior: Conexión con el Visor
        grp_control = QGroupBox("📅 PERIODO DE CONTROL (VINCULADO AL CRONOGRAMA)")
        l_control = QHBoxLayout(grp_control)
        
        self.lbl_info_corte = QLabel("Fecha de corte actual: <b>No calculada</b>")
        self.lbl_info_corte.setFont(QFont("Segoe UI", 12))
        l_control.addWidget(self.lbl_info_corte)
        
        btn_calcular = QPushButton("🔄 TRAER DATOS DEL CORTE Y CALCULAR")
        btn_calcular.setStyleSheet("background-color: #8e44ad; color: white; font-weight: bold; padding: 10px; border-radius: 5px;")
        btn_calcular.clicked.connect(self.calcular_evm)
        l_control.addWidget(btn_calcular)
        
        layout_principal.addWidget(grp_control)

        # 2. Tarjetas de Indicadores (PV, EV, AC)
        layout_tarjetas = QHBoxLayout()
        
        self.tarjeta_pv = QGroupBox("VALOR PLANEADO (PV)")
        self.tarjeta_pv.setStyleSheet("QGroupBox { background-color: #e8f8f5; border: 2px solid #1abc9c; border-radius: 8px; font-weight: bold; }")
        l_pv = QVBoxLayout(self.tarjeta_pv)
        self.lbl_pv_val = QLabel("$ 0")
        self.lbl_pv_val.setFont(QFont("Segoe UI", 24, QFont.Weight.Bold))
        self.lbl_pv_val.setAlignment(Qt.AlignmentFlag.AlignCenter)
        l_pv.addWidget(self.lbl_pv_val)
        layout_tarjetas.addWidget(self.tarjeta_pv)

        self.tarjeta_ev = QGroupBox("VALOR GANADO (EV)")
        self.tarjeta_ev.setStyleSheet("QGroupBox { background-color: #eaf2f8; border: 2px solid #3498db; border-radius: 8px; font-weight: bold; }")
        l_ev = QVBoxLayout(self.tarjeta_ev)
        self.lbl_ev_val = QLabel("$ 0")
        self.lbl_ev_val.setFont(QFont("Segoe UI", 24, QFont.Weight.Bold))
        self.lbl_ev_val.setAlignment(Qt.AlignmentFlag.AlignCenter)
        l_ev.addWidget(self.lbl_ev_val)
        layout_tarjetas.addWidget(self.tarjeta_ev)

        self.tarjeta_ac = QGroupBox("COSTO ACTUAL (AC)")
        self.tarjeta_ac.setStyleSheet("QGroupBox { background-color: #fdedec; border: 2px solid #e74c3c; border-radius: 8px; font-weight: bold; }")
        l_ac = QVBoxLayout(self.tarjeta_ac)
        self.lbl_ac_val = QLabel("$ 0")
        self.lbl_ac_val.setFont(QFont("Segoe UI", 24, QFont.Weight.Bold))
        self.lbl_ac_val.setAlignment(Qt.AlignmentFlag.AlignCenter)
        l_ac.addWidget(self.lbl_ac_val)
        layout_tarjetas.addWidget(self.tarjeta_ac)

        layout_principal.addLayout(layout_tarjetas)
        
        # 3. Interpretación de la Salud del Proyecto
        self.grp_salud = QGroupBox("🏥 SALUD DEL PROYECTO")
        l_salud = QVBoxLayout(self.grp_salud)
        self.lbl_diagnostico = QLabel("Haz el 'Corte de Obra' en la pestaña Cronograma y luego presiona Calcular aquí.")
        self.lbl_diagnostico.setFont(QFont("Segoe UI", 12))
        self.lbl_diagnostico.setAlignment(Qt.AlignmentFlag.AlignCenter)
        l_salud.addWidget(self.lbl_diagnostico)
        layout_principal.addWidget(self.grp_salud)

        # 4. TABLA DE EXTRACCIÓN DEL CRONOGRAMA
        self.grp_tabla_evm = QGroupBox("📋 DETALLE DE TAREAS EN EL CORTE")
        l_tabla = QVBoxLayout(self.grp_tabla_evm)
        
        self.tabla_evm_tareas = QTableWidget(0, 7) 
        self.tabla_evm_tareas.setHorizontalHeaderLabels(["ID", "Nombre de Tarea", "Cant. Plan", "Valor Unit", "Valor Plan", "Cant. Ejec.", "Valor Ejec."])
        self.tabla_evm_tareas.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self.tabla_evm_tareas.setAlternatingRowColors(True)
        
        # Conectamos el vigilante de los cálculos
        self.tabla_evm_tareas.itemChanged.connect(self.recalcular_filas_evm)
        
        l_tabla.addWidget(self.tabla_evm_tareas)
        layout_principal.addWidget(self.grp_tabla_evm)

    def calcular_evm(self):
        # 1. LEER LA FECHA DESDE visor_2.py (Pestaña Cronograma)
        try:
            # 🔴 CORRECCIÓN DEFINITIVA: 
            # El visor guarda la fecha elegida en la variable 'fecha_linea_corte'.
            if hasattr(self.tab_cronograma, 'fecha_linea_corte') and self.tab_cronograma.fecha_linea_corte is not None:
                fecha_corte_qdate = self.tab_cronograma.fecha_linea_corte
            else:
                fecha_corte_qdate = QDate.currentDate() 
                
            fecha_corte_dt = fecha_corte_qdate.toPyDate()
            fecha_corte_pd = pd.to_datetime(fecha_corte_dt)
            self.lbl_info_corte.setText(f"Fecha de corte vinculada: <b>{fecha_corte_dt.strftime('%d/%m/%Y')}</b>")
        except Exception as e:
            QMessageBox.critical(self, "Error de Vinculación", f"No se pudo leer la fecha del visor: {e}")
            return

        # 2. CÁLCULO DEL COSTO ACTUAL (AC)
        total_ac = 0
        try:
            ruta_mat = self.ruta(self.file_mat)
            if os.path.exists(ruta_mat):
                df_mat = pd.read_csv(ruta_mat)
                if 'Fecha_Uso' not in df_mat.columns:
                    df_mat['Fecha_Uso'] = df_mat['Fecha']
                df_mat['Fecha_DT'] = pd.to_datetime(df_mat['Fecha_Uso'], dayfirst=True, errors='coerce')
                gastos_validos = df_mat[df_mat['Fecha_DT'] <= fecha_corte_pd]
                total_ac += gastos_validos['Total'].sum()
                
            ruta_mo = self.ruta(self.file_mo)
            if os.path.exists(ruta_mo):
                df_mo = pd.read_csv(ruta_mo)
                df_mo['Fecha_DT'] = pd.to_datetime(df_mo['Fecha'], dayfirst=True, errors='coerce')
                gastos_validos_mo = df_mo[df_mo['Fecha_DT'] <= fecha_corte_pd]
                total_ac += gastos_validos_mo['Total'].sum()
        except Exception as e:
            print("Error calculando AC:", e)

        self.lbl_ac_val.setText(f"$ {total_ac:,.0f}")

        # =========================================================
        # 3. REPLICAR LA TABLA DEL CORTE DE OBRA (CRONOGRAMA)
        # =========================================================
        self.tabla_evm_tareas.blockSignals(True) # Apagar vigilante mientras se construye la tabla
        self.tabla_evm_tareas.setRowCount(0)
        
        if hasattr(self.tab_cronograma, 'tree'):
            arbol_origen = self.tab_cronograma.tree
            filas = arbol_origen.topLevelItemCount()
            
            # Función rápida para bloquear celdas individuales
            def celda_bloqueada(texto):
                item = QTableWidgetItem(texto)
                item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEditable) 
                return item

            for i in range(filas):
                item_origen = arbol_origen.topLevelItem(i)
                row_idx = self.tabla_evm_tareas.rowCount()
                self.tabla_evm_tareas.insertRow(row_idx)
                
                # 1. Capturamos los textos (RESPETANDO LOS ESPACIOS VACÍOS)
                val_id = item_origen.text(0) if item_origen.text(0) else ""
                val_nombre = item_origen.text(1).strip() if item_origen.text(1) else ""
                val_plan_str = item_origen.text(2).strip() if item_origen.text(2) else "" 
                por_esp_str = item_origen.text(4).strip() if item_origen.text(4) else ""
                val_ejec = item_origen.text(5).strip() if item_origen.text(5) else ""
                
                # 2. Si es un capítulo, en blanco. Si tiene datos, calculamos.
                if val_plan_str == "":
                    val_plan_final = ""
                else:
                    try:
                        p_limpio = "".join(c for c in val_plan_str.replace(",", ".") if c.isdigit() or c == ".")
                        e_limpio = "".join(c for c in por_esp_str.replace(",", ".") if c.isdigit() or c == ".")
                        
                        if p_limpio.count('.') > 1:
                            partes = p_limpio.rsplit('.', 1)
                            p_limpio = partes[0].replace('.', '') + '.' + partes[1]
                        if e_limpio.count('.') > 1:
                            partes = e_limpio.rsplit('.', 1)
                            e_limpio = partes[0].replace('.', '') + '.' + partes[1]

                        if not p_limpio: p_limpio = "0"
                        if not e_limpio: e_limpio = "0"
                        
                        plan_num = float(p_limpio)
                        esp_num = float(e_limpio)
                        
                        cant_esperada_num = plan_num * (esp_num / 100.0)
                        
                        if cant_esperada_num.is_integer():
                            val_plan_final = str(int(cant_esperada_num))
                        else:
                            val_plan_final = f"{cant_esperada_num:.2f}"
                            
                    except Exception:
                        val_plan_final = val_plan_str

                # --- LLENAMOS LA TABLA ---
                
                # 0. ID
                self.tabla_evm_tareas.setItem(row_idx, 0, celda_bloqueada(val_id))
                
                # 1. Nombre 
                self.tabla_evm_tareas.setItem(row_idx, 1, celda_bloqueada(val_nombre))
                
                # 2. Cant. Plan (Esperada)
                item_plan = celda_bloqueada(val_plan_final)
                item_plan.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                self.tabla_evm_tareas.setItem(row_idx, 2, item_plan)
                
                # 3. Valor Unit (La editable)
                item_unit = QTableWidgetItem("")
                if val_plan_final != "":
                    item_unit.setBackground(QColor("#fffbcc")) 
                self.tabla_evm_tareas.setItem(row_idx, 3, item_unit) 
                
                # 4. Valor Plan 
                self.tabla_evm_tareas.setItem(row_idx, 4, celda_bloqueada("")) 
                
                # 5. Cant. Ejec.
                item_ejec = celda_bloqueada(val_ejec)
                item_ejec.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                self.tabla_evm_tareas.setItem(row_idx, 5, item_ejec) 
                
                # 6. Valor Ejec. 
                self.tabla_evm_tareas.setItem(row_idx, 6, celda_bloqueada("")) 

                # --- 3. TOQUE PRO: NEGRILLA PARA LOS CAPÍTULOS ---
                if val_plan_str == "":
                    font_capitulo = QFont()
                    font_capitulo.setBold(True)
                    # Recorremos las 7 columnas de esa fila para ponerlas en negrilla
                    for col in range(7):
                        celda = self.tabla_evm_tareas.item(row_idx, col)
                        if celda:
                            celda.setFont(font_capitulo)

        else:
            print("No se encontró 'self.tree' en el cronograma")

        self.tabla_evm_tareas.blockSignals(False) # Prender vigilante
        
        # Actualizamos las tarjetas apenas se cargue la tabla para que queden limpias
        self.actualizar_tarjetas_evm()

    def recalcular_filas_evm(self, item):
        # Solo calculamos si el cambio ocurrió en la columna 3 (Valor Unit)
        if item.column() == 3:
            fila = item.row()
            
            txt_unit = item.text().replace("$", "").replace(",", "").strip()
            try: val_unit = float(txt_unit) if txt_unit else 0.0
            except ValueError: val_unit = 0.0
                
            txt_plan = self.tabla_evm_tareas.item(fila, 2).text().replace(",", "").strip()
            try: cant_plan = float(txt_plan) if txt_plan else 0.0
            except ValueError: cant_plan = 0.0
                
            txt_ejec = self.tabla_evm_tareas.item(fila, 5).text().replace(",", "").strip()
            try: cant_ejec = float(txt_ejec) if txt_ejec else 0.0
            except ValueError: cant_ejec = 0.0
                
            valor_plan_total = cant_plan * val_unit
            valor_ejec_total = cant_ejec * val_unit
            
            self.tabla_evm_tareas.blockSignals(True) 
            
            def celda_bloqueada(texto):
                nuevo_item = QTableWidgetItem(texto)
                nuevo_item.setFlags(nuevo_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
                return nuevo_item
            
            self.tabla_evm_tareas.setItem(fila, 4, celda_bloqueada(f"${valor_plan_total:,.0f}"))
            self.tabla_evm_tareas.setItem(fila, 6, celda_bloqueada(f"${valor_ejec_total:,.0f}"))
            
            self.tabla_evm_tareas.blockSignals(False) 
            
            # Disparamos la calculadora maestra
            self.actualizar_tarjetas_evm()

    def actualizar_tarjetas_evm(self):
        total_pv = 0.0
        total_ev = 0.0
        
        # 1. Recorrer toda la tabla y sumar las columnas 4 (Plan) y 6 (Ejec)
        for fila in range(self.tabla_evm_tareas.rowCount()):
            item_plan = self.tabla_evm_tareas.item(fila, 4)
            if item_plan and item_plan.text():
                txt_plan = item_plan.text().replace("$", "").replace(",", "").strip()
                try: total_pv += float(txt_plan)
                except ValueError: pass
                
            item_ejec = self.tabla_evm_tareas.item(fila, 6)
            if item_ejec and item_ejec.text():
                txt_ejec = item_ejec.text().replace("$", "").replace(",", "").strip()
                try: total_ev += float(txt_ejec)
                except ValueError: pass
                
        # 2. Actualizar las tarjetas visuales superiores
        self.lbl_pv_val.setText(f"$ {total_pv:,.0f}")
        self.lbl_ev_val.setText(f"$ {total_ev:,.0f}")
        
        # 3. Leer el AC (Costo Actual) para poder actualizar el diagnóstico
        txt_ac = self.lbl_ac_val.text().replace("$", "").replace(",", "").strip()
        try: total_ac = float(txt_ac)
        except ValueError: total_ac = 0.0
        
        # 4. Recalcular SPI y CPI (Salud del Proyecto)
        if total_pv > 0 or total_ac > 0:
            spi = (total_ev / total_pv) if total_pv > 0 else 0
            cpi = (total_ev / total_ac) if total_ac > 0 else 0
            
            txt_cronograma = "🔴 ATRASADO" if spi < 1 else "🟢 ADELANTADO"
            txt_costos = "🔴 PERDIENDO DINERO (SOBRECOSTO)" if cpi < 1 else "🟢 GANANDO DINERO (AHORRO)"
            
            diagnostico = f"<b>SPI (Cronograma):</b> {spi:.2f} ➔ {txt_cronograma}<br><br><b>CPI (Costos):</b> {cpi:.2f} ➔ {txt_costos}"
            self.lbl_diagnostico.setText(diagnostico)
        else:
            self.lbl_diagnostico.setText("Escribe los Valores Unitarios en la tabla para calcular la salud del proyecto.")


if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    
    # --- HOJA DE ESTILOS CLARA Y MODERNA ---
    estilo_claro = """
    QMainWindow, QWidget {
        background-color: #f0f2f5; 
        color: #2c3e50; 
        font-family: "Segoe UI", Arial, sans-serif;
    }
    QGroupBox {
        background-color: #ffffff; 
        border: 1px solid #bdc3c7;
        border-radius: 6px;
        margin-top: 15px;
    }
    QGroupBox::title {
        subcontrol-origin: margin;
        subcontrol-position: top left;
        padding: 0 5px;
        color: #2980b9; 
        font-weight: bold;
    }
    QTableWidget {
        background-color: #ffffff;
        alternate-background-color: #f9f9f9;
        gridline-color: #dcdde1;
        selection-background-color: #3498db;
        selection-color: white;
    }
    QHeaderView::section {
        background-color: #e1e8ed;
        color: #2c3e50;
        padding: 5px;
        border: 1px solid #dcdde1;
        font-weight: bold;
    }
    QLineEdit, QComboBox, QDateEdit {
        background-color: #ffffff;
        border: 1px solid #bdc3c7;
        padding: 6px;
        border-radius: 4px;
        color: #2c3e50;
    }
    QLineEdit:focus, QComboBox:focus {
        border: 2px solid #3498db; 
    }
    QTabWidget::pane {
        border: 1px solid #bdc3c7;
        background-color: #ffffff;
    }
    QTabBar::tab {
        background-color: #ecf0f1;
        color: #7f8c8d;
        padding: 10px 20px;
        border-top-left-radius: 4px;
        border-top-right-radius: 4px;
        margin-right: 2px;
    }
    QTabBar::tab:selected {
        background-color: #ffffff;
        color: #2980b9;
        font-weight: bold;
        border-bottom: 2px solid #ffffff;
    }
    """
    app.setStyleSheet(estilo_claro)
    
    window = SistemaContable()
    window.show()
    sys.exit(app.exec())