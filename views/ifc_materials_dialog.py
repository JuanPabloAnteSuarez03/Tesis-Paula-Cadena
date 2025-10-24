from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QFileDialog,
    QTableWidget, QTableWidgetItem, QHeaderView, QMessageBox
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

        # Tabla de Acero de Refuerzo (única tabla solicitada)
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
        layout.addWidget(self.rebar_table)

        # Botones
        btns = QHBoxLayout()
        btn_open = QPushButton("Abrir IFC…")
        btn_export_rebar = QPushButton("Exportar CSV acero…")
        btn_export_rebar_cons = QPushButton("Exportar CSV acero (consolidado)…")
        btn_close = QPushButton("Cerrar")
        btn_open.clicked.connect(self._open_ifc)
        btn_export_rebar.clicked.connect(self._export_rebar_csv)
        btn_export_rebar_cons.clicked.connect(self._export_rebar_csv_consolidated)
        btn_close.clicked.connect(self.accept)
        btns.addWidget(btn_open)
        btns.addStretch(1)
        btns.addWidget(btn_export_rebar)
        btns.addWidget(btn_export_rebar_cons)
        btns.addWidget(btn_close)
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
        try:
            model = ifcopenshell.open(path)
        except Exception as e:
            QMessageBox.critical(self, "Error", f"No se pudo abrir el IFC:\n{e}")
            return

        self._populate_from_model(model)

    def _populate_from_model(self, ifc):
        self.rebar_table.setRowCount(0)

        # Escalas de unidades → normalizamos a m, m2, m3 y kg
        length_scale = self._get_length_scale_m(ifc)
        area_scale = self._get_area_scale_m2(ifc, fallback=length_scale ** 2)
        volume_scale = self._get_volume_scale_m3(ifc, fallback=length_scale ** 3)
        mass_scale = self._get_mass_scale_kg(ifc)

        def add_row(elem_name, guid, ifc_type, mat_name, unit, thickness, qty):
            r = self.table.rowCount()
            self.table.insertRow(r)
            for c, val in enumerate([elem_name, guid, ifc_type, mat_name, unit, thickness, qty]):
                item = QTableWidgetItem("" if val is None else str(val))
                item.setFlags(Qt.ItemFlag.ItemIsSelectable | Qt.ItemFlag.ItemIsEnabled)
                self.table.setItem(r, c, item)

        def get_qto(elem, names):
            for rel in (elem.IsDefinedBy or []):
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
            return None

        def get_material_layers(elem):
            for rel in (elem.HasAssociations or []):
                if rel.is_a("IfcRelAssociatesMaterial"):
                    m = rel.RelatingMaterial
                    if not m:
                        return []
                    if m.is_a("IfcMaterial"):
                        return [{"name": m.Name, "thickness": None}]
                    if m.is_a("IfcMaterialLayerSetUsage"):
                        layers = m.ForLayerSet.MaterialLayers or []
                        return [{"name": (lyr.Material.Name if lyr.Material else None),
                                 "thickness": (lyr.LayerThickness or 0) * length_scale} for lyr in layers]
                    if m.is_a("IfcMaterialLayerSet"):
                        layers = m.MaterialLayers or []
                        return [{"name": (lyr.Material.Name if lyr.Material else None),
                                 "thickness": (lyr.LayerThickness or 0) * length_scale} for lyr in layers]
                    if m.is_a("IfcMaterialConstituentSet"):
                        consts = m.MaterialConstituents or []
                        return [{"name": (c.Material.Name if c.Material else None), "thickness": None} for c in consts]
            return []

        # Poblar tabla de acero de refuerzo
        try:
            self._populate_rebar_from_model(ifc)
        except Exception:
            # Evitar que un fallo en acero rompa la extracción de materiales
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

    def _get_length_scale_m(self, ifc):
        try:
            uas = ifc.by_type("IfcUnitAssignment")
            if not uas:
                return 1.0
            ua = uas[0]
            for u in ua.Units or []:
                # IfcSIUnit for length
                if getattr(u, 'UnitType', None) and u.UnitType == 'LENGTHUNIT':
                    prefix = getattr(u, 'Prefix', None)
                    name = getattr(u, 'Name', None)
                    # Default metre
                    if name == 'METRE' and not prefix:
                        return 1.0
                    # Common prefixes
                    scale = 1.0
                    if prefix == 'MILLI':
                        scale = 0.001
                    elif prefix == 'CENTI':
                        scale = 0.01
                    elif prefix == 'DECI':
                        scale = 0.1
                    elif prefix == 'KILO':
                        scale = 1000.0
                    return scale
        except Exception:
            pass
        return 1.0

    def _get_area_scale_m2(self, ifc, fallback: float = 1.0):
        try:
            uas = ifc.by_type("IfcUnitAssignment")
            if not uas:
                return fallback
            ua = uas[0]
            for u in ua.Units or []:
                if getattr(u, 'UnitType', None) and u.UnitType == 'AREAUNIT':
                    prefix = getattr(u, 'Prefix', None)
                    name = getattr(u, 'Name', None)
                    # Default square metre
                    if name == 'SQUARE_METRE' and not prefix:
                        return 1.0
                    scale = 1.0
                    if prefix == 'MILLI':
                        scale = 0.001 ** 2
                    elif prefix == 'CENTI':
                        scale = 0.01 ** 2
                    elif prefix == 'DECI':
                        scale = 0.1 ** 2
                    elif prefix == 'KILO':
                        scale = 1000.0 ** 2
                    return scale
        except Exception:
            pass
        return fallback

    def _get_volume_scale_m3(self, ifc, fallback: float = 1.0):
        try:
            uas = ifc.by_type("IfcUnitAssignment")
            if not uas:
                return fallback
            ua = uas[0]
            for u in ua.Units or []:
                if getattr(u, 'UnitType', None) and u.UnitType == 'VOLUMEUNIT':
                    prefix = getattr(u, 'Prefix', None)
                    name = getattr(u, 'Name', None)
                    # Default cubic metre
                    if name == 'CUBIC_METRE' and not prefix:
                        return 1.0
                    scale = 1.0
                    if prefix == 'MILLI':
                        scale = 0.001 ** 3
                    elif prefix == 'CENTI':
                        scale = 0.01 ** 3
                    elif prefix == 'DECI':
                        scale = 0.1 ** 3
                    elif prefix == 'KILO':
                        scale = 1000.0 ** 3
                    return scale
        except Exception:
            pass
        return fallback

    def _get_mass_scale_kg(self, ifc):
        try:
            uas = ifc.by_type("IfcUnitAssignment")
            if not uas:
                return 1.0
            ua = uas[0]
            for u in ua.Units or []:
                if getattr(u, 'UnitType', None) and u.UnitType == 'MASSUNIT':
                    prefix = getattr(u, 'Prefix', None)
                    name = getattr(u, 'Name', None)
                    # Default kilogram
                    if name == 'GRAM':
                        return 0.001
                    if name == 'KILOGRAM' and not prefix:
                        return 1.0
                    if name == 'TONNE':
                        return 1000.0
                    # Handle SI prefixes if provided
                    scale = 1.0
                    if prefix == 'MILLI':
                        scale = 0.001
                    elif prefix == 'CENTI':
                        scale = 0.01
                    elif prefix == 'DECI':
                        scale = 0.1
                    elif prefix == 'KILO':
                        scale = 1000.0
                    return scale
        except Exception:
            pass
        return 1.0


    # ==========================
    #   Rebar (Acero de refuerzo)
    # ==========================
    def _populate_rebar_from_model(self, ifc):
        # Unidades
        length_scale = self._get_length_scale_m(ifc)

        # Mapa de diámetro nominal a número de varilla (NBR/ACI aproximado)
        # El IFC típicamente trae diámetro en mm. Aquí cubrimos tamaños comunes.
        def bar_number_from_diameter_mm(d):
            mapping = {
                6: "#2", 8: "#2", 10: "#3", 12: "#4", 13: "#4", 16: "#5",
                19: "#6", 22: "#7", 25: "#8", 29: "#9", 32: "#10", 36: "#11",
            }
            # Redondeo al entero más cercano para emparejar
            return mapping.get(int(round(d)), f"Ø{d:.0f}mm")

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
            if ('foundation' in t) or ('footing' in t) or ('ciment' in t) or ('base' in t):
                return "Cimentación estructural"
            if ('framing' in t) or ('beam' in t) or ('column' in t) or ('wall' in t) or ('slab' in t) or ('floor' in t) or ('structural' in t):
                return "Armazón estructural"
            if ('steel' in t) or ('metal' in t):
                return "Estructura metálica"
            return None

        # Recolectar barras
        rows = []
        for rb in ifc.by_type("IfcReinforcingBar"):
            host = find_host_product(rb)
            # Priorizar categoría desde propiedades (instancia/tipo/grupo) y mapear a español
            host_cat_text = (
                _get_pset_string_from_obj(rb, {"Host Category", "HostCategory", "Rebar Host Category", "Category"})
                or _get_pset_string_from_type(rb, {"Host Category", "HostCategory", "Rebar Host Category", "Category"})
                or _get_group_pset_string_from_assignments(rb, {"Host Category", "HostCategory", "Rebar Host Category", "Category"})
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

            rows.append({
                "categoria": cat,
                "cantidad": qty_bars,
                "long_mm": length_mm,
                "long_m": length_m,
                "diam": (inch_txt if inch_txt else (f"{dia_mm:.0f} mm" if dia_mm else "")),
                "num": num_bar,
                "kgpm": (round(kgpm, 3) if kgpm else None),
                "kg_total": (round(total_kg, 2) if total_kg is not None else None),
            })

        # Escribir filas
        for rdata in rows:
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
