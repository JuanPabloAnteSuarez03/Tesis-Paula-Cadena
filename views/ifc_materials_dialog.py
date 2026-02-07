from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QFileDialog,
    QTableWidget, QTableWidgetItem, QHeaderView, QMessageBox, QTabWidget,
    QApplication, QWidget, QProgressBar
)
from PyQt6.QtCore import Qt

import csv

try:
    import ifcopenshell
except Exception as e:
    ifcopenshell = None


class IFCMaterialsDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Importar IFC - Materiales")
        self.resize(900, 600)

        layout = QVBoxLayout(self)

        info = QLabel(
            "Seleccione un archivo IFC (IFC2x3 o IFC4).\n"
            "Se listarán materiales por elemento con cantidades estimadas (m3 si hay datos)."
        )
        info.setWordWrap(True)
        layout.addWidget(info)

        # Barra de progreso inline (oculta por defecto)
        self.progress_widget = QWidget(self)
        prog_layout = QHBoxLayout(self.progress_widget)
        prog_layout.setContentsMargins(0, 0, 0, 0)
        prog_layout.setSpacing(8)
        self.progress_label = QLabel("Procesando IFC...")
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 0)  # indeterminado
        prog_layout.addWidget(self.progress_label)
        prog_layout.addWidget(self.progress_bar, 1)
        self.progress_widget.setVisible(False)
        layout.addWidget(self.progress_widget)

        # Pestañas
        self.tabs = QTabWidget(self)

        # Tabla de Concreto
        self.concrete_table = QTableWidget(self)
        self.concrete_table.setColumnCount(5)
        self.concrete_table.setHorizontalHeaderLabels([
            "Categoría de anfitrión", "Tipo", "Longitud (m)", "Área (m²)", "Volumen (m³)"
        ])
        cheader = self.concrete_table.horizontalHeader()
        cheader.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        cheader.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        cheader.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        cheader.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        cheader.setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)

        # Tabla de Acero de Refuerzo
        self.rebar_table = QTableWidget(self)
        self.rebar_table.setColumnCount(8)
        self.rebar_table.setHorizontalHeaderLabels([
            "Categoría de anfitrión", "Cantidad", "Longitud (mm)", "Longitud (m)",
            "Diámetro de Varilla", "Número de Varilla", "PESO Kg/m", "Peso total por elemento Kg"
        ])
        rheader = self.rebar_table.horizontalHeader()
        rheader.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        rheader.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        rheader.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        rheader.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        rheader.setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)
        rheader.setSectionResizeMode(5, QHeaderView.ResizeMode.ResizeToContents)
        rheader.setSectionResizeMode(6, QHeaderView.ResizeMode.ResizeToContents)
        rheader.setSectionResizeMode(7, QHeaderView.ResizeMode.ResizeToContents)
        self.tabs.addTab(self.concrete_table, "Concreto")
        self.tabs.addTab(self.rebar_table, "Acero (Rebar)")
        layout.addWidget(self.tabs)

        # Botones
        btns = QHBoxLayout()
        self.btn_open = QPushButton("Abrir IFC…")
        self.btn_generate = QPushButton("Generar ítems…")
        self.btn_close = QPushButton("Cerrar")
        self.btn_open.clicked.connect(self._open_ifc)
        self.btn_generate.clicked.connect(self._generate_items_from_ifc)
        self.btn_close.clicked.connect(self.accept)
        btns.addWidget(self.btn_open)
        btns.addStretch(1)
        btns.addWidget(self.btn_generate)
        btns.addWidget(self.btn_close)
        layout.addLayout(btns)

        if not ifcopenshell:
            QMessageBox.warning(self, "Dependencia faltante",
                                "No se pudo importar ifcopenshell. Instale con: pip install ifcopenshell")

    def _open_ifc(self):
        if not ifcopenshell:
            return
        path, _ = QFileDialog.getOpenFileName(self, "Abrir IFC", "", "IFC Files (*.ifc *.ifczip *.ifcZIP)")
        if not path:
            return
        
        self._show_progress("Leyendo archivo IFC... (esto puede tardar unos segundos)")
        QApplication.processEvents()
        
        try:
            # Abrir el modelo. ifcopenshell.open es síncrono y pesado.
            model = ifcopenshell.open(path)
        except Exception as e:
            self._hide_progress()
            QMessageBox.critical(self, "Error", f"No se pudo abrir el IFC:\n{e}")
            return

        try:
            self._populate_from_model(model)
        finally:
            self._hide_progress()

    def _generate_items_from_ifc(self):
        """
        Consolida los datos actuales y abre 'Importar por Texto' prellenado:
        - Siempre agrega una fila con item = "1".
        - ACERO: se agrega directamente al presupuesto con el total de Kg del proyecto.
        """

        # 1) Total de acero (Kg)
        total_kg = 0.0
        try:
            for r in range(self.rebar_table.rowCount()):
                c0 = self.rebar_table.item(r, 0)
                if c0 and str(c0.text()).upper().startswith("TOTAL KILOS"):
                    continue

                c_kg = self.rebar_table.item(r, 7)  # Peso total por elemento Kg
                if not c_kg:
                    continue

                try:
                    total_kg += float(c_kg.text().strip().replace(',', '.'))
                except Exception:
                    continue

            # Fallback: leer fila TOTAL KILOS si existe
            if total_kg <= 0:
                for r in range(self.rebar_table.rowCount()):
                    c0 = self.rebar_table.item(r, 0)
                    if c0 and str(c0.text()).upper().startswith("TOTAL KILOS"):
                        c_last = self.rebar_table.item(r, 7)
                        if c_last:
                            try:
                                total_kg = float(c_last.text().strip().replace(',', '.'))
                            except Exception:
                                pass
                        break
        except Exception:
            total_kg = 0.0

        # 2) Agregar acero directamente al presupuesto
        try:
            parent = self.parent()
            if total_kg > 0 and hasattr(parent, 'add_ifc_rebar_analysis'):
                parent.add_ifc_rebar_analysis(round(total_kg, 2))
        except Exception:
            pass

        # 3) Preparar UNA sola fila para Importar por Texto
        prefill_rows = [{
            'item': '1',  # <-- ESTE ERA EL PROBLEMA: debe ser '1', no ''
            'descripcion': '',
            'unidad': '',
            'cantidad': ''
        }]

        # 4) Abrir Importar por Texto
        try:
            parent = self.parent()
            if hasattr(parent, "open_import_text_dialog"):
                parent.open_import_text_dialog(prefill_rows=prefill_rows, append=True)
            else:
                from .importar_por_texto_dialog import ImportarPorTextoDialog
                dlg = ImportarPorTextoDialog(self, prefill_rows=prefill_rows)
                dlg.exec()
        except Exception as e:
            QMessageBox.critical(self, "Error", f"No se pudo abrir Importar por Texto:\n{e}")


    def _populate_from_model(self, ifc):
        self.concrete_table.setRowCount(0)
        self.rebar_table.setRowCount(0)
        
        self._update_progress("Detectando unidades y escalas...")
        QApplication.processEvents()

        # Escalas de unidades → normalizamos a m, m2, m3 y kg
        # Buscamos IfcUnitAssignment una sola vez para ahorrar tiempo
        uas = ifc.by_type("IfcUnitAssignment")
        ua = uas[0] if uas else None

        length_scale = self._extract_length_scale(ua)
        area_scale = self._extract_area_scale(ua, fallback=length_scale ** 2)
        volume_scale = self._extract_volume_scale(ua, fallback=length_scale ** 3)
        mass_scale = self._extract_mass_scale(ua)

        def add_row(elem_name, guid, ifc_type, mat_name, unit, thickness, qty):
            r = self.concrete_table.rowCount()
            self.concrete_table.insertRow(r)
            # ...
            for c, val in enumerate([elem_name, guid, ifc_type, mat_name, unit, thickness, qty]):
                item = QTableWidgetItem("" if val is None else str(val))
                item.setFlags(Qt.ItemFlag.ItemIsSelectable | Qt.ItemFlag.ItemIsEnabled)
                self.concrete_table.setItem(r, c, item)

        def get_qto(elem, names):
            return self._get_qto(elem, names, length_scale, area_scale, volume_scale, mass_scale)

        def get_material_layers(elem):
            for rel in (getattr(elem, 'HasAssociations', None) or []):
                if rel.is_a("IfcRelAssociatesMaterial"):
                    m = rel.RelatingMaterial
                    if not m:
                        return []
                    if m.is_a("IfcMaterial"):
                        return [{"name": getattr(m, 'Name', None), "thickness": None}]
                    if m.is_a("IfcMaterialLayerSetUsage"):
                        layers = getattr(m.ForLayerSet, 'MaterialLayers', None) or []
                        return [{"name": (lyr.Material.Name if lyr.Material and getattr(lyr.Material, 'Name', None) else None),
                                 "thickness": (getattr(lyr, 'LayerThickness', 0) or 0) * length_scale} for lyr in layers]
                    if m.is_a("IfcMaterialLayerSet"):
                        layers = getattr(m, 'MaterialLayers', None) or []
                        return [{"name": (lyr.Material.Name if lyr.Material and getattr(lyr.Material, 'Name', None) else None),
                                 "thickness": (getattr(lyr, 'LayerThickness', 0) or 0) * length_scale} for lyr in layers]
                    if m.is_a("IfcMaterialConstituentSet"):
                        consts = getattr(m, 'MaterialConstituents', None) or []
                        return [{"name": (c.Material.Name if c.Material and getattr(c.Material, 'Name', None) else None), "thickness": None} for c in consts]
            return []

        self._update_progress("Procesando concreto...")
        QApplication.processEvents()
        # Poblar tabla de concreto
        try:
            self._populate_concrete_from_model(ifc, length_scale, area_scale, volume_scale, mass_scale)
        except Exception as e:
            print(f"Error en populate_concrete: {e}")

        self._update_progress("Procesando acero de refuerzo...")
        QApplication.processEvents()
        # Poblar tabla de acero de refuerzo
        try:
            self._populate_rebar_from_model(ifc, length_scale)
        except Exception as e:
            print(f"Error en populate_rebar: {e}")
            pass

    def _show_progress(self, text: str):
        try:
            self.progress_label.setText(text)
            self.progress_widget.setVisible(True)
            self.btn_open.setEnabled(False)
            self.btn_generate.setEnabled(False)
            QApplication.processEvents()
        except Exception:
            pass

    def _update_progress(self, text: str):
        try:
            self.progress_label.setText(text)
            QApplication.processEvents()
        except Exception:
            pass

    def _hide_progress(self):
        try:
            self.progress_widget.setVisible(False)
            self.btn_open.setEnabled(True)
            self.btn_generate.setEnabled(True)
            QApplication.processEvents()
        except Exception:
            pass

    def _export_csv(self):
        if self.table.rowCount() == 0:
            QMessageBox.information(self, "Exportar", "No hay datos para exportar.")
            return
        path, _ = QFileDialog.getSaveFileName(self, "Exportar CSV", "materiales_ifc.csv", "CSV Files (*.csv)")
        if not path:
            return
        with open(path, 'w', newline='', encoding='utf-8') as f:
            w = csv.writer(f)
            headers = [self.table.horizontalHeaderItem(i).text() for i in range(self.table.columnCount())]
            w.writerow(headers)
            for r in range(self.table.rowCount()):
                row = []
                for c in range(self.table.columnCount()):
                    it = self.table.item(r, c)
                    row.append(it.text() if it else "")
                w.writerow(row)

    def _export_csv_consolidated(self):
        if self.table.rowCount() == 0:
            QMessageBox.information(self, "Exportar", "No hay datos para exportar.")
            return
        path, _ = QFileDialog.getSaveFileName(self, "Exportar CSV consolidado", "materiales_ifc_consolidado.csv", "CSV Files (*.csv)")
        if not path:
            return
        totals = {}
        for r in range(self.table.rowCount()):
            mat = (self.table.item(r, 3).text() if self.table.item(r, 3) else "").strip()
            unit = (self.table.item(r, 4).text() if self.table.item(r, 4) else "").strip()
            qty_text = (self.table.item(r, 6).text() if self.table.item(r, 6) else "").strip()
            if not mat or not unit or not qty_text:
                continue
            try:
                qty = float(qty_text)
            except ValueError:
                continue
            key = (mat, unit)
            totals[key] = totals.get(key, 0.0) + qty
        with open(path, 'w', newline='', encoding='utf-8') as f:
            w = csv.writer(f)
            w.writerow(["Material", "Unidad", "Cantidad"])
            for (mat, unit), qty in sorted(totals.items()):
                w.writerow([mat, unit, f"{qty}"])

    # ==== Concreto ====
    def _populate_concrete_from_model(self, ifc, length_scale: float, area_scale: float, volume_scale: float, mass_scale: float):
        # Helpers para edificio y nivel
        # Ya no usamos edificio/nivel; mantenemos la función por compatibilidad si fuera necesario.
        def get_building_and_level(elem):
            return "", ""

        def _clean_type_text(text):
            try:
                import re
                s = str(text or "")
                # Mantener prefijo (p. ej., 'Basic Wall:'), solo quitar sufijo numérico ':123456'
                m = re.match(r'^(.*?):\s*\d+\s*$', s)
                if m:
                    return m.group(1)
                return re.sub(r':\s*\d+\s*$', '', s)
            except Exception:
                return str(text)

        def elem_type_name(elem):
            # Nombre del tipo si existe, sino Name del elemento
            try:
                for rel in (getattr(elem, 'IsTypedBy', None) or []):
                    t = rel.RelatingType
                    if t and getattr(t, 'Name', None):
                        return _clean_type_text(t.Name)
            except Exception:
                pass
            try:
                return _clean_type_text(getattr(elem, 'Name', '') or '')
            except Exception:
                return ''

        def host_category(elem):
            et = elem.is_a()
            if et in { 'IfcFooting', 'IfcPile' }:
                return 'Cimentación estructural'
            if et == 'IfcColumn':
                return 'Pilar estructural'
            if et in { 'IfcStair', 'IfcStairFlight' }:
                return 'Escaleras'
            # Slab, Beam, Wall, etc.
            return 'Armazón estructural'

        # Elementos de concreto típicos
        element_types = [
            'IfcFooting','IfcPile','IfcSlab','IfcWall','IfcBeam','IfcColumn','IfcStair','IfcStairFlight'
        ]

        # Detectar elementos de acero estructural para excluirlos del listado de Concreto
        def _collect_material_names(elem):
            names = []
            try:
                for rel in (getattr(elem, 'HasAssociations', None) or []):
                    if rel.is_a('IfcRelAssociatesMaterial'):
                        m = rel.RelatingMaterial
                        if not m:
                            continue
                        if m.is_a('IfcMaterial'):
                            if getattr(m, 'Name', None):
                                names.append(str(m.Name))
                        elif m.is_a('IfcMaterialLayerSetUsage'):
                            layers = getattr(m.ForLayerSet, 'MaterialLayers', None) or []
                            for lyr in layers:
                                mat = getattr(lyr, 'Material', None)
                                if mat and getattr(mat, 'Name', None):
                                    names.append(str(mat.Name))
                        elif m.is_a('IfcMaterialLayerSet'):
                            layers = getattr(m, 'MaterialLayers', None) or []
                            for lyr in layers:
                                mat = getattr(lyr, 'Material', None)
                                if mat and getattr(mat, 'Name', None):
                                    names.append(str(mat.Name))
                        elif m.is_a('IfcMaterialConstituentSet'):
                            consts = getattr(m, 'MaterialConstituents', None) or []
                            for c in consts:
                                mat = getattr(c, 'Material', None)
                                if mat and getattr(mat, 'Name', None):
                                    names.append(str(mat.Name))
            except Exception:
                pass
            return [n for n in names if n]

        steel_keywords = {
            'ipe','ipn','hea','heb','hem','upn','steel','acero',
            'h_perfiles','h-perfiles','perfil h','h perfiles','viga i','i-beam','h-beam','wide flange','steel deck'
        }

        def _is_stair(elem):
            try:
                return elem.is_a('IfcStair') or elem.is_a('IfcStairFlight')
            except Exception:
                return False

        # Sumar QTO de componentes (recursivo en la cadena de agregados)
        def _sum_child_qto(elem, names, _seen=None):
            try:
                if _seen is None:
                    _seen = set()
                if id(elem) in _seen:
                    return None
                _seen.add(id(elem))
                total = 0.0
                found_any = False
                for rel in (getattr(elem, 'IsDecomposedBy', None) or []):
                    if rel.is_a('IfcRelAggregates'):
                        related = getattr(rel, 'RelatedObjects', None) or []
                        for j, ch in enumerate(related):
                            if j % 50 == 0:
                                QApplication.processEvents()
                            # Valor directo en el hijo
                            val = self._get_qto(ch, names, length_scale, area_scale, volume_scale, mass_scale)
                            if val is not None:
                                total += float(val)
                                found_any = True
                            # Recursión en nietos
                            sub = _sum_child_qto(ch, names, _seen)
                            if sub not in (None, 0):
                                total += float(sub)
                                found_any = True
                return total if found_any else None
            except Exception:
                return None

        # Longitud como IfcPositiveLengthMeasure en Psets (instancia o tipo)
        def get_positive_length(elem):
            try:
                for rel in (getattr(elem, 'IsDefinedBy', None) or []):
                    if rel.is_a('IfcRelDefinesByProperties'):
                        pdef = rel.RelatingPropertyDefinition
                        if pdef and pdef.is_a('IfcPropertySet'):
                            for p in (pdef.HasProperties or []):
                                if p.is_a('IfcPropertySingleValue'):
                                    nv = getattr(p, 'NominalValue', None)
                                    if nv is not None and getattr(nv, 'is_a', lambda *_: False)('IfcPositiveLengthMeasure'):
                                        try:
                                            return float(getattr(nv, 'wrappedValue', None)) * length_scale
                                        except Exception:
                                            pass
            except Exception:
                pass
            try:
                for rel in (getattr(elem, 'IsTypedBy', None) or []):
                    t = rel.RelatingType
                    if not t:
                        continue
                    for pset in (getattr(t, 'HasPropertySets', None) or []):
                        if pset.is_a('IfcPropertySet'):
                            for p in (pset.HasProperties or []):
                                if p.is_a('IfcPropertySingleValue'):
                                    nv = getattr(p, 'NominalValue', None)
                                    if nv is not None and getattr(nv, 'is_a', lambda *_: False)('IfcPositiveLengthMeasure'):
                                        try:
                                            return float(getattr(nv, 'wrappedValue', None)) * length_scale
                                        except Exception:
                                            pass
            except Exception:
                pass
            return None

        rows = []
        all_elems = []
        for et in element_types:
            self._update_progress(f"Buscando elementos de concreto ({et})...")
            all_elems.extend(ifc.by_type(et))
            QApplication.processEvents()
        
        total_count = len(all_elems)
        self.progress_bar.setRange(0, total_count)
        
        # Optimización: pausar repintado de tabla mientras se llena
        self.concrete_table.setUpdatesEnabled(False)
        self.concrete_table.setRowCount(0)
        
        for i, elem in enumerate(all_elems):
            if i % 1 == 0: # Para concreto, procesar eventos en cada elemento
                self.progress_bar.setValue(i)
                if i % 10 == 0:
                    self._update_progress(f"Procesando concreto: {i}/{total_count} elementos...")
                else:
                    QApplication.processEvents()
                
            # Excluir vigas/elementos de acero estructural (IPE, HEA, HEB, etc.) del listado de Concreto
            etype_text = (elem_type_name(elem) or '')
            objtype_text = str(getattr(elem, 'ObjectType', '') or '')
            mats_text = ' '.join(_collect_material_names(elem))
            txt_all = f"{etype_text} {objtype_text} {mats_text}".lower()
            if any(k in txt_all for k in steel_keywords):
                continue
            # Volumen: sólo GrossVolume / NetVolume
            v = self._get_qto(
                elem,
                { 'GrossVolume', 'NetVolume' },
                length_scale, area_scale, volume_scale, mass_scale
            )
            # Fallback específico para escaleras: algunos modelos usan 'Volume'
            if v in (None, 0) and _is_stair(elem):
                v_alt = self._get_qto(elem, { 'Volume', 'BodyVolume' }, length_scale, area_scale, volume_scale, mass_scale)
                if v_alt not in (None, 0):
                    v = v_alt
            if v in (None, 0):
                # Para elementos compuestos (p.ej. IfcStair), sumar volumen desde sus componentes
                v_comp = _sum_child_qto(elem, { 'GrossVolume', 'NetVolume', 'Volume', 'BodyVolume' })
                if v_comp not in (None, 0):
                    v = v_comp
            # Área: CrossSectionArea / OuterSurfaceArea, con respaldo mínimo a GrossArea y GrossFootprintArea
            a = self._get_qto(
                elem,
                { 'CrossSectionArea', 'OuterSurfaceArea', 'GrossArea', 'GrossFootprintArea' },
                length_scale, area_scale, volume_scale, mass_scale
            )
            # Fallback área para escaleras
            if a in (None, 0) and _is_stair(elem):
                a_alt = self._get_qto(elem, { 'NetArea', 'Area', 'SideArea' }, length_scale, area_scale, volume_scale, mass_scale)
                if a_alt not in (None, 0):
                    a = a_alt
            if a in (None, 0):
                a_comp = _sum_child_qto(elem, { 'CrossSectionArea', 'OuterSurfaceArea', 'GrossArea', 'GrossFootprintArea', 'NetArea', 'Area', 'SideArea' })
                if a_comp not in (None, 0):
                    a = a_comp
            # Longitud: únicamente IfcPositiveLengthMeasure en Psets
            l = get_positive_length(elem)
            # Si no hay longitud pero sí volumen y área, derivar L = V / A
            if (l is None or l == 0) and (a not in (None, 0)) and (v not in (None, 0)):
                try:
                    l = float(v) / float(a)
                except Exception:
                    pass
            # Si sigue faltando volumen en escaleras, aproximar con área de sección × longitud
            if _is_stair(elem) and (v in (None, 0)) and (l not in (None, 0)):
                a_section = self._get_qto(elem, { 'CrossSectionArea' }, length_scale, area_scale, volume_scale, mass_scale)
                if a_section not in (None, 0):
                    try:
                        v = float(a_section) * float(l)
                    except Exception:
                        pass

            bld, lvl = get_building_and_level(elem)
            rows.append({
                'bld': bld,
                'lvl': lvl,
                'cat': host_category(elem),
                'type': elem_type_name(elem),
                'len': l,
                'area': a,
                'vol': v,
            })

        # Orden solo por categoría
        rows.sort(key=lambda r: (r['cat'], r['type']))

        # Escribir filas y subtotales por nivel
        def write_row(vals):
            r = self.concrete_table.rowCount()
            self.concrete_table.insertRow(r)
            for c, v in enumerate(vals):
                item = QTableWidgetItem("" if v is None else str(v))
                item.setFlags(Qt.ItemFlag.ItemIsSelectable | Qt.ItemFlag.ItemIsEnabled)
                self.concrete_table.setItem(r, c, item)

        total_project = 0.0
        i = 0
        current_cat = None
        cat_subtotal = 0.0
        while i < len(rows):
            if i % 20 == 0:
                self._update_progress(f"Escribiendo tabla de concreto: {i}/{len(rows)}...")
            r = rows[i]
            if r['cat'] != current_cat:
                if current_cat is not None:
                    write_row(["", "", "", "", f"{cat_subtotal:.2f}"])
                    total_project += cat_subtotal
                    cat_subtotal = 0.0
                current_cat = r['cat']
                # Encabezado de categoría
                write_row([current_cat, "", "", "", ""])
            # Fila elemento
            write_row([
                r['cat'], _clean_type_text(r['type']),
                (f"{float(r['len']):.3f}" if r['len'] is not None else "0.000"),
                (f"{float(r['area']):.3f}" if r['area'] is not None else "0.000"),
                (f"{float(r['vol']):.3f}" if r['vol'] is not None else "0.000")
            ])
            try:
                cat_subtotal += float(r['vol'] or 0.0)
            except Exception:
                pass
            i += 1
        # Cerrar última categoría
        if current_cat is not None:
            write_row(["", "", "", "", f"{cat_subtotal:.2f}"])
            total_project += cat_subtotal

        # Fila total proyecto
        write_row(["TOTAL PROYECTO", "", "", "", f"{total_project:.2f}"])
        
        self.concrete_table.setUpdatesEnabled(True)
        self.concrete_table.viewport().update()

    def _export_concrete_csv(self):
        if self.concrete_table.rowCount() == 0:
            QMessageBox.information(self, "Exportar", "No hay datos de concreto para exportar.")
            return
        path, _ = QFileDialog.getSaveFileName(self, "Exportar CSV concreto", "concreto_ifc.csv", "CSV Files (*.csv)")
        if not path:
            return
        with open(path, 'w', newline='', encoding='utf-8') as f:
            w = csv.writer(f)
            headers = [self.concrete_table.horizontalHeaderItem(i).text() for i in range(self.concrete_table.columnCount())]
            w.writerow(headers)
            for r in range(self.concrete_table.rowCount()):
                row = []
                for c in range(self.concrete_table.columnCount()):
                    it = self.concrete_table.item(r, c)
                    row.append(it.text() if it else "")
                w.writerow(row)

    def _export_concrete_csv_consolidated(self):
        if self.concrete_table.rowCount() == 0:
            QMessageBox.information(self, "Exportar", "No hay datos de concreto para exportar.")
            return
        path, _ = QFileDialog.getSaveFileName(self, "Exportar CSV concreto (consolidado)", "concreto_ifc_consolidado.csv", "CSV Files (*.csv)")
        if not path:
            return
        # Consolidar por categoría
        totals = {}
        for r in range(self.concrete_table.rowCount()):
            cat = (self.concrete_table.item(r, 0).text() if self.concrete_table.item(r, 0) else "").strip()
            vol_text = (self.concrete_table.item(r, 4).text() if self.concrete_table.item(r, 4) else "").strip()
            try:
                vol = float(vol_text.replace(',', '.'))
            except Exception:
                continue
            totals[cat] = totals.get(cat, 0.0) + vol
        with open(path, 'w', newline='', encoding='utf-8') as f:
            w = csv.writer(f)
            w.writerow(["Categoría de anfitrión", "Volumen (m3)"])
            for cat, v in sorted(totals.items()):
                w.writerow([cat, f"{v:.2f}"])

    def _extract_length_scale(self, ua):
        if not ua: return 1.0
        try:
            for u in ua.Units or []:
                if getattr(u, 'UnitType', None) and u.UnitType == 'LENGTHUNIT':
                    prefix = getattr(u, 'Prefix', None)
                    name = getattr(u, 'Name', None)
                    if name == 'METRE' and not prefix: return 1.0
                    scale = 1.0
                    if prefix == 'MILLI': scale = 0.001
                    elif prefix == 'CENTI': scale = 0.01
                    elif prefix == 'DECI': scale = 0.1
                    elif prefix == 'KILO': scale = 1000.0
                    return scale
        except Exception: pass
        return 1.0

    def _extract_area_scale(self, ua, fallback: float = 1.0):
        if not ua: return fallback
        try:
            for u in ua.Units or []:
                if getattr(u, 'UnitType', None) and u.UnitType == 'AREAUNIT':
                    prefix = getattr(u, 'Prefix', None)
                    name = getattr(u, 'Name', None)
                    if name == 'SQUARE_METRE' and not prefix: return 1.0
                    scale = 1.0
                    if prefix == 'MILLI': scale = 0.001 ** 2
                    elif prefix == 'CENTI': scale = 0.01 ** 2
                    elif prefix == 'DECI': scale = 0.1 ** 2
                    elif prefix == 'KILO': scale = 1000.0 ** 2
                    return scale
        except Exception: pass
        return fallback

    def _extract_volume_scale(self, ua, fallback: float = 1.0):
        if not ua: return fallback
        try:
            for u in ua.Units or []:
                if getattr(u, 'UnitType', None) and u.UnitType == 'VOLUMEUNIT':
                    prefix = getattr(u, 'Prefix', None)
                    name = getattr(u, 'Name', None)
                    if name == 'CUBIC_METRE' and not prefix: return 1.0
                    scale = 1.0
                    if prefix == 'MILLI': scale = 0.001 ** 3
                    elif prefix == 'CENTI': scale = 0.01 ** 3
                    elif prefix == 'DECI': scale = 0.1 ** 3
                    elif prefix == 'KILO': scale = 1000.0 ** 3
                    return scale
        except Exception: pass
        return fallback

    def _extract_mass_scale(self, ua):
        if not ua: return 1.0
        try:
            for u in ua.Units or []:
                if getattr(u, 'UnitType', None) and u.UnitType == 'MASSUNIT':
                    prefix = getattr(u, 'Prefix', None)
                    name = getattr(u, 'Name', None)
                    if name == 'GRAM': return 0.001
                    if name == 'KILOGRAM' and not prefix: return 1.0
                    if name == 'TONNE': return 1000.0
                    scale = 1.0
                    if prefix == 'MILLI': scale = 0.001
                    elif prefix == 'CENTI': scale = 0.01
                    elif prefix == 'DECI': scale = 0.1
                    elif prefix == 'KILO': scale = 1000.0
                    return scale
        except Exception: pass
        return 1.0

    # ==========================
    #   Rebar (Acero de refuerzo)
    # ==========================
    def _get_qto(self, elem, names, length_scale: float, area_scale: float, volume_scale: float, mass_scale: float):
        try:
            for rel in (getattr(elem, 'IsDefinedBy', None) or []):
                if rel.is_a("IfcRelDefinesByProperties"):
                    pdef = rel.RelatingPropertyDefinition
                    if pdef and pdef.is_a("IfcElementQuantity"):
                        for q in (pdef.Quantities or []):
                            if q.Name in names:
                                if q.is_a("IfcQuantityArea"):
                                    return float(q.AreaValue) * area_scale
                                if q.is_a("IfcQuantityVolume"):
                                    return float(q.VolumeValue) * volume_scale
                                if q.is_a("IfcQuantityLength"):
                                    return float(q.LengthValue) * length_scale
                                if q.is_a("IfcQuantityWeight"):
                                    return float(q.WeightValue) * mass_scale
                                if q.is_a("IfcQuantityCount"):
                                    return float(q.CountValue)
        except Exception:
            pass
        return None
    def _populate_rebar_from_model(self, ifc, length_scale: float):
        # Unidades ya recibidas por parámetro

        # Mapa de diámetro nominal a número de varilla (NBR/ACI aproximado)
        # El IFC típicamente trae diámetro en mm. Aquí cubrimos tamaños comunes.
        def bar_number_from_diameter_mm(d):
            mapping = {
                6: "#2", 8: "#2", 10: "#3", 12: "#4", 13: "#4", 16: "#5",
                19: "#6", 22: "#7", 25: "#8", 29: "#9", 32: "#10", 36: "#11",
            }
            # Redondeo al entero más cercano para emparejar
            return mapping.get(int(round(d)), f"Ø{d:.0f}mm")

        # Texto en pulgadas por número de varilla (ACI)
        number_to_inch_text = {
            "#2": '1/4\"',
            "#3": '3/8\"',
            "#4": '1/2\"',
            "#5": '5/8\"',
            "#6": '3/4\"',
            "#7": '7/8\"',
            "#8": '1\"',
            "#9": '1 1/8\"',
            "#10": '1 1/4\"',
            "#11": '1 3/8\"',
        }

        # Fórmula estándar de peso lineal del acero (kg/m): 0.006165 * d^2 con d en mm
        def kg_per_m_from_diameter_mm(d):
            return 0.006165 * (d ** 2)

        # Intentar agrupar por elemento anfitrión (categoría)
        def map_host_to_spanish_category(host):
            try:
                htype = host.is_a() if host else None
                if htype in {"IfcFooting", "IfcPile"}:
                    return "Cimentación estructural"
                if htype == "IfcSlab":
                    ptype = getattr(host, 'PredefinedType', None)
                    if str(ptype) in {"BASESLAB", "FOOTING"}:
                        return "Cimentación estructural"
                if htype == "IfcColumn":
                    return "Pilar estructural"
                if htype in {"IfcStair", "IfcStairFlight"}:
                    return "Escaleras"
                return "Armazón estructural"
            except Exception:
                return "Armazón estructural"

        def find_host_product(elem):
            # 1) Asignaciones a producto
            try:
                for rel in (elem.HasAssignments or []):
                    if rel.is_a("IfcRelAssignsToProduct") and getattr(rel, 'RelatingProduct', None):
                        return rel.RelatingProduct
            except Exception:
                pass
            # 2) Parte de un agregado (rebar dentro de un ensamble)
            try:
                for rel in (elem.Decomposes or []):
                    if rel.is_a("IfcRelAggregates") and getattr(rel, 'RelatingObject', None):
                        return rel.RelatingObject
            except Exception:
                pass
            # 3) Conexiones a elementos
            try:
                for rel in (elem.ConnectedFrom or []):
                    if getattr(rel, 'RelatingElement', None):
                        return rel.RelatingElement
                for rel in (elem.ConnectedTo or []):
                    if getattr(rel, 'RelatedElement', None):
                        return rel.RelatedElement
            except Exception:
                pass
            return None

        # Buscar en propiedades/psets un texto tipo '5/8" #5'
        def find_reference_text(obj):
            try:
                for rel in (getattr(obj, 'IsDefinedBy', None) or []):
                    if rel.is_a("IfcRelDefinesByProperties"):
                        pdef = rel.RelatingPropertyDefinition
                        if pdef and pdef.is_a("IfcPropertySet"):
                            for p in (pdef.HasProperties or []):
                                if p.is_a("IfcPropertySingleValue") and p.Name in {"Reference", "Bar Size", "BarSize", "ReferenceId"}:
                                    try:
                                        val = p.NominalValue.wrappedValue if p.NominalValue else None
                                    except Exception:
                                        val = None
                                    if val:
                                        return str(val)
            except Exception:
                pass
            # Tipo
            try:
                for rel in (getattr(obj, 'IsTypedBy', None) or []):
                    t = rel.RelatingType
                    if t:
                        # psets del tipo
                        for pset in (getattr(t, 'HasPropertySets', None) or []):
                            if pset.is_a("IfcPropertySet"):
                                for p in (pset.HasProperties or []):
                                    if p.is_a("IfcPropertySingleValue") and p.Name in {"Reference", "Bar Size", "BarSize", "ReferenceId"}:
                                        try:
                                            val = p.NominalValue.wrappedValue if p.NominalValue else None
                                        except Exception:
                                            val = None
                                        if val:
                                            return str(val)
                        # fallback: nombre del tipo
                        if getattr(t, 'Name', None):
                            return str(t.Name)
            except Exception:
                pass
            # fallback al nombre del objeto
            try:
                if getattr(obj, 'Name', None):
                    return str(obj.Name)
            except Exception:
                pass
            return None

        def parse_inch_and_bar(text: str):
            if not text:
                return None, None, None
            import re
            inch_txt = None
            num_bar = None
            dia_mm = None
            # 5/8" y #5
            m = re.search(r'(\d+)\s*/\s*(\d+)\s*"', text)
            if m:
                num = int(m.group(1)); den = int(m.group(2))
                inch_val = num / den
                dia_mm = inch_val * 25.4
                inch_txt = f"{num}/{den}\""
            m2 = re.search(r'#\s*(\d+)', text)
            if m2:
                num_bar = f"#{int(m2.group(1))}"
            return inch_txt, num_bar, dia_mm

        # Conversión inversa aproximada por número de varilla→mm (ACI)
        number_to_mm = {
            '#2': 6.35, '#3': 9.525, '#4': 12.7, '#5': 15.875, '#6': 19.05,
            '#7': 22.225, '#8': 25.4, '#9': 28.65, '#10': 32.26, '#11': 35.81,
        }

        # Utilidades para leer valores numéricos desde Psets (instancia y tipo)
        def _get_pset_numeric_from_obj(obj, names):
            try:
                for rel in (getattr(obj, 'IsDefinedBy', None) or []):
                    if rel.is_a("IfcRelDefinesByProperties"):
                        pdef = rel.RelatingPropertyDefinition
                        if pdef and pdef.is_a("IfcPropertySet"):
                            for p in (pdef.HasProperties or []):
                                if p.is_a("IfcPropertySingleValue") and p.Name in names:
                                    nv = getattr(p, 'NominalValue', None)
                                    if nv is None:
                                        continue
                                    val = getattr(nv, 'wrappedValue', None)
                                    if val is None:
                                        continue
                                    try:
                                        return float(val)
                                    except Exception:
                                        try:
                                            return int(val)
                                        except Exception:
                                            pass
            except Exception:
                pass
            return None

        def _get_pset_numeric_from_type(obj, names):
            try:
                for rel in (getattr(obj, 'IsTypedBy', None) or []):
                    t = rel.RelatingType
                    if not t:
                        continue
                    for pset in (getattr(t, 'HasPropertySets', None) or []):
                        if pset.is_a("IfcPropertySet"):
                            for p in (pset.HasProperties or []):
                                if p.is_a("IfcPropertySingleValue") and p.Name in names:
                                    nv = getattr(p, 'NominalValue', None)
                                    if nv is None:
                                        continue
                                    val = getattr(nv, 'wrappedValue', None)
                                    if val is None:
                                        continue
                                    try:
                                        return float(val)
                                    except Exception:
                                        try:
                                            return int(val)
                                        except Exception:
                                            pass
            except Exception:
                pass
            return None

        # Utilidades para leer strings desde Psets o Grupos
        def _get_pset_string_from_obj(obj, names):
            try:
                for rel in (getattr(obj, 'IsDefinedBy', None) or []):
                    if rel.is_a("IfcRelDefinesByProperties"):
                        pdef = rel.RelatingPropertyDefinition
                        if pdef and pdef.is_a("IfcPropertySet"):
                            for p in (pdef.HasProperties or []):
                                if p.is_a("IfcPropertySingleValue") and p.Name in names:
                                    nv = getattr(p, 'NominalValue', None)
                                    if nv is None:
                                        continue
                                    val = getattr(nv, 'wrappedValue', None)
                                    if val is not None:
                                        return str(val)
            except Exception:
                pass
            return None

        def _get_pset_string_from_type(obj, names):
            try:
                for rel in (getattr(obj, 'IsTypedBy', None) or []):
                    t = rel.RelatingType
                    if not t:
                        continue
                    for pset in (getattr(t, 'HasPropertySets', None) or []):
                        if pset.is_a("IfcPropertySet"):
                            for p in (pset.HasProperties or []):
                                if p.is_a("IfcPropertySingleValue") and p.Name in names:
                                    nv = getattr(p, 'NominalValue', None)
                                    if nv is None:
                                        continue
                                    val = getattr(nv, 'wrappedValue', None)
                                    if val is not None:
                                        return str(val)
            except Exception:
                pass
            return None

        def _get_group_pset_string_from_assignments(obj, names):
            try:
                for rel in (getattr(obj, 'HasAssignments', None) or []):
                    if rel.is_a("IfcRelAssignsToGroup"):
                        g = rel.RelatingGroup
                        if not g:
                            continue
                        # Psets del grupo
                        for grel in (getattr(g, 'IsDefinedBy', None) or []):
                            if grel.is_a("IfcRelDefinesByProperties"):
                                pdef = grel.RelatingPropertyDefinition
                                if pdef and pdef.is_a("IfcPropertySet"):
                                    for p in (pdef.HasProperties or []):
                                        if p.is_a("IfcPropertySingleValue") and p.Name in names:
                                            nv = getattr(p, 'NominalValue', None)
                                            if nv is None:
                                                continue
                                            val = getattr(nv, 'wrappedValue', None)
                                            if val is not None:
                                                return str(val)
                        # Fallback: nombre u ObjectType del grupo
                        if getattr(g, 'Name', None):
                            return str(g.Name)
                        if getattr(g, 'ObjectType', None):
                            return str(g.ObjectType)
            except Exception:
                pass
            return None

        def _map_category_text_to_spanish(text):
            if not text:
                return None
            t = str(text).lower()
            # Revit exports we found in IFC: 'Structural Foundation', 'Structural Framing', 'Structural Column', 'Stairs', 'Floor', 'Wall'
            if ('structural foundation' in t) or ('foundation' in t) or ('footing' in t):
                return "Cimentación estructural"
            if ('structural column' in t) or ('column' in t):
                return "Pilar estructural"
            if ('stairs' in t) or ('stair' in t):
                return "Escaleras"
            if ('structural framing' in t) or ('framing' in t) or ('beam' in t):
                return "Armazón estructural"
            # Fallbacks from building elements that could appear as host categories
            if ('floor' in t) or ('slab' in t) or ('wall' in t):
                return "Armazón estructural"
            return None

        # Recolectar barras
        rows = []
        all_rebar = ifc.by_type("IfcReinforcingBar")
        total_count = len(all_rebar)
        self.progress_bar.setRange(0, total_count)
        
        # Optimización: pausar repintado
        self.rebar_table.setUpdatesEnabled(False)
        self.rebar_table.setRowCount(0)
        
        for i, rb in enumerate(all_rebar):
            if i % 20 == 0: # Actualizar UI cada 20 barras (suelen ser muchas)
                self.progress_bar.setValue(i)
                QApplication.processEvents()
                
            host = find_host_product(rb)
            # Priorizar categoría desde propiedades (instancia/tipo/grupo) y mapear a español
            host_cat_text = (
                _get_pset_string_from_obj(rb, {"Host Category", "HostCategory", "Rebar Host Category", "Category"})
                or _get_pset_string_from_type(rb, {"Host Category", "HostCategory", "Rebar Host Category", "Category"})
                or _get_group_pset_string_from_assignments(rb, {"Host Category", "HostCategory", "Rebar Host Category", "Category"})
            )
            if not host_cat_text and host:
                host_cat_text = (
                    _get_pset_string_from_obj(host, {"Host Category", "HostCategory", "Category"})
                    or _get_pset_string_from_type(host, {"Host Category", "HostCategory", "Category"})
                )
            cat = _map_category_text_to_spanish(host_cat_text) or map_host_to_spanish_category(host)
            guid = getattr(rb, 'GlobalId', '')
            # Longitud: tomar del QTO si existe, si no, usar nominal length
            length_m = None
            # QTO
            try:
                for rel in (rb.IsDefinedBy or []):
                    if rel.is_a("IfcRelDefinesByProperties") and rel.RelatingPropertyDefinition and rel.RelatingPropertyDefinition.is_a("IfcElementQuantity"):
                        for q in rel.RelatingPropertyDefinition.Quantities or []:
                            if q.is_a("IfcQuantityLength") and q.Name in {"Length", "NetLength", "GrossLength"}:
                                length_m = float(q.LengthValue) * length_scale
                                break
                    if length_m is not None:
                        break
            except Exception:
                pass
            # Atributos directos del elemento (IFC2x3 trae BarLength)
            if length_m is None:
                try:
                    blen = getattr(rb, 'BarLength', None)
                    if blen is not None:
                        length_m = float(blen) * length_scale
                except Exception:
                    pass
            if length_m is None:
                try:
                    nlen = getattr(rb, 'NominalLength', None)
                    if nlen is not None:
                        length_m = float(nlen) * length_scale
                except Exception:
                    pass
            # Propiedades en Psets (objeto y tipo)
            if length_m is None:
                try:
                    for rel in (rb.IsDefinedBy or []):
                        if rel.is_a("IfcRelDefinesByProperties"):
                            pdef = rel.RelatingPropertyDefinition
                            if pdef and pdef.is_a("IfcPropertySet"):
                                for p in (pdef.HasProperties or []):
                                    if p.is_a("IfcPropertySingleValue") and p.Name in {"Length", "BarLength", "NominalLength"}:
                                        try:
                                            val = p.NominalValue.wrappedValue if p.NominalValue else None
                                        except Exception:
                                            val = None
                                        if val is not None:
                                            length_m = float(val) * length_scale
                                            break
                            if length_m is not None:
                                break
                except Exception:
                    pass
            if length_m is None:
                try:
                    for rel in (rb.IsTypedBy or []):
                        t = rel.RelatingType
                        if not t:
                            continue
                        for pset in (getattr(t, 'HasPropertySets', None) or []):
                            if pset.is_a("IfcPropertySet"):
                                for p in (pset.HasProperties or []):
                                    if p.is_a("IfcPropertySingleValue") and p.Name in {"Length", "BarLength", "NominalLength"}:
                                        try:
                                            val = p.NominalValue.wrappedValue if p.NominalValue else None
                                        except Exception:
                                            val = None
                                        if val is not None:
                                            length_m = float(val) * length_scale
                                            break
                            if length_m is not None:
                                break
                        if length_m is not None:
                            break
                except Exception:
                    pass

            # Diámetro nominal en mm
            dia_mm = None
            try:
                nd = getattr(rb, 'NominalDiameter', None)
                if nd is not None:
                    # NominalDiameter está en unidades de longitud del modelo
                    dia_mm = float(nd) * (length_scale * 1000.0)  # m -> mm
            except Exception:
                pass

            inch_txt, num_from_text, dia_from_text_mm = parse_inch_and_bar(find_reference_text(rb))
            # Si el texto trae pulgadas o número, preferirlos
            if dia_from_text_mm:
                dia_mm = dia_from_text_mm
            num_bar = num_from_text or (bar_number_from_diameter_mm(dia_mm) if dia_mm else "")
            if not dia_mm and num_bar in number_to_mm:
                dia_mm = number_to_mm[num_bar]
            kgpm = kg_per_m_from_diameter_mm(dia_mm) if dia_mm else 0.0

            # Cantidad de barras (Count) si disponible
            qty_bars = 1
            try:
                # Some models use Count in QTO
                for rel in (rb.IsDefinedBy or []):
                    if rel.is_a("IfcRelDefinesByProperties") and rel.RelatingPropertyDefinition and rel.RelatingPropertyDefinition.is_a("IfcElementQuantity"):
                        for q in rel.RelatingPropertyDefinition.Quantities or []:
                            if q.is_a("IfcQuantityCount") and q.Name in {"Count", "NumberOfItems"}:
                                qty_bars = int(q.CountValue)
                                break
            except Exception:
                pass

            # Leer Quantity desde Psets (instancia y tipo) cuando existe como IFCINTEGER
            p_qty = _get_pset_numeric_from_obj(rb, {"Quantity", "Quantity By Rebar Set", "Number"})
            if p_qty is None:
                p_qty = _get_pset_numeric_from_type(rb, {"Quantity", "Quantity By Rebar Set", "Number"})
            if p_qty is not None:
                try:
                    qty_bars = int(round(float(p_qty)))
                except Exception:
                    pass

            # Si sólo tenemos longitud total en Psets, dividir por Quantity para obtener longitud por barra
            if length_m is None:
                total_len_obj = _get_pset_numeric_from_obj(rb, {"Total Bar Length"})
                total_len_typ = _get_pset_numeric_from_type(rb, {"Total Bar Length"})
                total_len = total_len_obj if total_len_obj is not None else total_len_typ
                if total_len is not None:
                    try:
                        if qty_bars and qty_bars > 0:
                            length_m = (float(total_len) * length_scale) / float(qty_bars)
                        else:
                            length_m = float(total_len) * length_scale
                    except Exception:
                        pass

            length_mm = length_m * 1000.0 if length_m is not None else None
            total_kg = (kgpm * length_m * qty_bars) if (kgpm and length_m) else None

            # Construir texto de diámetro y filtrar elementos con diámetro en mm
            if not inch_txt and num_bar in number_to_inch_text:
                inch_txt = number_to_inch_text[num_bar]
            diam_str = inch_txt if inch_txt else (f"{dia_mm:.0f} mm" if dia_mm else "")
            if diam_str and "mm" in diam_str.lower():
                # Omitir filas cuyo diámetro está expresado en mm
                continue

            rows.append({
                "categoria": cat,
                "cantidad": qty_bars,
                "long_mm": length_mm,
                "long_m": length_m,
                "diam": diam_str,
                "num": num_bar,
                "kgpm": (round(kgpm, 3) if kgpm else None),
                "kg_total": (round(total_kg, 2) if total_kg is not None else None),
            })

        # Escribir filas
        for i, rdata in enumerate(rows):
            if i % 100 == 0:
                QApplication.processEvents()
            r = self.rebar_table.rowCount()
            self.rebar_table.insertRow(r)
            for c, val in enumerate([
                rdata["categoria"], rdata["cantidad"],
                ("" if rdata["long_mm"] is None else f"{rdata['long_mm']:.0f}"),
                ("" if rdata["long_m"] is None else f"{rdata['long_m']:.2f}"),
                rdata["diam"], rdata["num"],
                ("" if rdata["kgpm"] is None else f"{rdata['kgpm']:.3f}"),
                ("" if rdata["kg_total"] is None else f"{rdata['kg_total']:.2f}")
            ]):
                item = QTableWidgetItem(str(val))
                item.setFlags(Qt.ItemFlag.ItemIsSelectable | Qt.ItemFlag.ItemIsEnabled)
                self.rebar_table.setItem(r, c, item)

        # Fila de TOTAL DE KILOS DEL PROYECTO
        try:
            grand_kg = sum((r.get("kg_total") or 0.0) for r in rows)
            r = self.rebar_table.rowCount()
            self.rebar_table.insertRow(r)
            total_label = "TOTAL KILOS DEL PROYECTO"
            values = [total_label, "", "", "", "", "", "", f"{grand_kg:.2f}"]
            for c, val in enumerate(values):
                item = QTableWidgetItem(str(val))
                item.setFlags(Qt.ItemFlag.ItemIsSelectable | Qt.ItemFlag.ItemIsEnabled)
                self.rebar_table.setItem(r, c, item)
        except Exception:
            pass
            
        self.rebar_table.setUpdatesEnabled(True)
        self.rebar_table.viewport().update()

    def _export_rebar_csv(self):
        if self.rebar_table.rowCount() == 0:
            QMessageBox.information(self, "Exportar", "No hay datos de acero para exportar.")
            return
        path, _ = QFileDialog.getSaveFileName(self, "Exportar CSV acero", "acero_ifc.csv", "CSV Files (*.csv)")
        if not path:
            return
        with open(path, 'w', newline='', encoding='utf-8') as f:
            w = csv.writer(f)
            headers = [self.rebar_table.horizontalHeaderItem(i).text() for i in range(self.rebar_table.columnCount())]
            w.writerow(headers)
            for r in range(self.rebar_table.rowCount()):
                row = []
                for c in range(self.rebar_table.columnCount()):
                    it = self.rebar_table.item(r, c)
                    row.append(it.text() if it else "")
                w.writerow(row)

    def _export_rebar_csv_consolidated(self):
        if self.rebar_table.rowCount() == 0:
            QMessageBox.information(self, "Exportar", "No hay datos de acero para exportar.")
            return
        path, _ = QFileDialog.getSaveFileName(self, "Exportar CSV acero (consolidado)", "acero_ifc_consolidado.csv", "CSV Files (*.csv)")
        if not path:
            return
        # Consolidar por diámetro/número de varilla
        totals = {}
        for r in range(self.rebar_table.rowCount()):
            num = (self.rebar_table.item(r, 5).text() if self.rebar_table.item(r, 5) else "").strip()
            kg_text = (self.rebar_table.item(r, 7).text() if self.rebar_table.item(r, 7) else "").strip()
            if not num or not kg_text:
                continue
            try:
                kg = float(kg_text)
            except ValueError:
                continue
            totals[num] = totals.get(num, 0.0) + kg
        with open(path, 'w', newline='', encoding='utf-8') as f:
            w = csv.writer(f)
            w.writerow(["Número de Varilla", "Peso total (Kg)"])
            for num, kg in sorted(totals.items()):
                w.writerow([num, f"{kg:.2f}"])
