import json
from typing import List, Dict
from PySide6 import QtCore, QtWidgets
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure

from planner import PlateType, enumerate_symmetric_combos

def _set_chinese_font():
    from matplotlib import font_manager, rcParams
    candidates = [
        "Microsoft YaHei UI", "Microsoft YaHei", "SimHei",
        "Noto Sans CJK SC", "Source Han Sans SC", "Apple Symbols",
        "Arial Unicode MS"
    ]
    avail = {f.name for f in font_manager.fontManager.ttflist}
    for name in candidates:
        if name in avail:
            rcParams["font.family"] = name
            break
    rcParams["axes.unicode_minus"] = False

def fmt_num(x: float) -> str:
    s = f"{x:.3f}".rstrip("0").rstrip(".")
    return s if s else "0"

class PlateDiagramCanvas(FigureCanvas):
    def __init__(self, parent=None):
        _set_chinese_font()
        self.fig = Figure(figsize=(7, 2.6), dpi=100)
        super().__init__(self.fig)
        self.ax = self.fig.add_subplot(111)
        self.fig.tight_layout()

    def draw_layout(self, plates: List[PlateType], per_side_counts: Dict[int, int], side_len_cm: float):
        from matplotlib.patches import Rectangle
        self.ax.clear()
        # Guides
        self.ax.axvline(0, linestyle="--", linewidth=1)
        self.ax.axvline(-side_len_cm, linestyle=":", linewidth=1)
        self.ax.axvline(side_len_cm, linestyle=":", linewidth=1)
        # Rod
        rod = Rectangle((-side_len_cm, 0.45), 2*side_len_cm, 0.10, fill=True, alpha=0.15)
        self.ax.add_patch(rod)

        # Order for display
        order = sorted(per_side_counts.items(), key=lambda kv: (-plates[kv[0]].weight, -plates[kv[0]].thickness))
        gap = 0.2  # visual gap (cm), display only
        plate_h = 0.60
        y0 = 0.25

        def draw_plate(x_left, width, label):
            from matplotlib.patches import Rectangle
            shrink = min(gap, width*0.3)
            x0 = x_left + shrink/2.0
            w  = max(0.01, width - shrink)
            rect = Rectangle((x0, y0), w, plate_h, fill=True, alpha=0.5)
            rect.set_linewidth(1.2)
            self.ax.add_patch(rect)
            self.ax.text(x0 + w/2.0, y0 + plate_h/2.0, label, ha="center", va="center", fontsize=9)

        # Left side
        cur = 0.0
        for idx, cnt in order:
            p = plates[idx]
            for _ in range(cnt):
                draw_plate(-cur - p.thickness, p.thickness, f"{p.weight:g} kg")
                cur += p.thickness
        # Right side
        cur = 0.0
        for idx, cnt in order:
            p = plates[idx]
            for _ in range(cnt):
                draw_plate(cur, p.thickness, f"{p.weight:g} kg")
                cur += p.thickness

        span = max(1.0, side_len_cm)
        self.ax.set_xlim(-span*1.2, span*1.2)
        self.ax.set_ylim(0, 1)
        self.ax.set_yticks([])
        self.ax.set_xlabel("从中心向左右（单位：cm）")
        self.ax.set_title("上片图（左右对称）")
        self.draw()

class MainWindow(QtWidgets.QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("哑铃/连接杆 组合计算器（上片图）— 增强版")
        self.resize(1200, 740)

        central = QtWidgets.QWidget()
        self.setCentralWidget(central)
        h = QtWidgets.QHBoxLayout(central)

        # Left: inventory & params
        left = QtWidgets.QVBoxLayout()
        h.addLayout(left, stretch=4)
        left.addWidget(QtWidgets.QLabel("杠片清单（重量kg / 厚度cm / 数量）"))
        self.table = QtWidgets.QTableWidget(0, 4)
        self.table.setHorizontalHeaderLabels(["重量(kg)", "厚度(cm)", "数量(片)", "标签(可选)"])
        self.table.horizontalHeader().setSectionResizeMode(QtWidgets.QHeaderView.Stretch)
        left.addWidget(self.table)

        row_btns = QtWidgets.QHBoxLayout()
        self.btn_add = QtWidgets.QPushButton("＋ 添加一行")
        self.btn_del = QtWidgets.QPushButton("－ 删除选中行")
        self.btn_sample = QtWidgets.QPushButton("载入示例清单")
        self.btn_load = QtWidgets.QPushButton("打开JSON清单…")
        self.btn_save = QtWidgets.QPushButton("保存JSON清单…")
        for b in (self.btn_add, self.btn_del, self.btn_sample, self.btn_load, self.btn_save):
            row_btns.addWidget(b)
        left.addLayout(row_btns)

        form = QtWidgets.QFormLayout()
        self.input_len_pair = QtWidgets.QDoubleSpinBox(); self.input_len_pair.setRange(0.0, 1000.0); self.input_len_pair.setDecimals(2); self.input_len_pair.setValue(21.0)
        self.input_len_conn = QtWidgets.QDoubleSpinBox(); self.input_len_conn.setRange(0.0, 1000.0); self.input_len_conn.setDecimals(2); self.input_len_conn.setValue(21.0)
        self.input_bar_pair = QtWidgets.QDoubleSpinBox(); self.input_bar_pair.setRange(0.0, 200.0); self.input_bar_pair.setDecimals(3); self.input_bar_pair.setValue(0.365)  # 默认单根哑铃杆
        self.input_bar_conn = QtWidgets.QDoubleSpinBox(); self.input_bar_conn.setRange(0.0, 200.0); self.input_bar_conn.setDecimals(3); self.input_bar_conn.setValue(1.0)    # 默认连接杆
        form.addRow("每侧可用长度（哑铃一对，cm）", self.input_len_pair)
        form.addRow("每侧可用长度（连接杆，cm）", self.input_len_conn)
        form.addRow("单根哑铃杆重量（kg）", self.input_bar_pair)
        form.addRow("连接杆（整根）重量（kg）", self.input_bar_conn)
        left.addLayout(form)

        self.btn_calc = QtWidgets.QPushButton("开始计算所有组合")
        left.addWidget(self.btn_calc)

        # Right: search + tabs + diagram
        right = QtWidgets.QVBoxLayout()
        h.addLayout(right, stretch=6)

        sr = QtWidgets.QHBoxLayout()
        self.search_edit = QtWidgets.QLineEdit(); self.search_edit.setPlaceholderText("搜索当前页面的重量（kg）…")
        self.btn_search = QtWidgets.QPushButton("搜索")
        sr.addWidget(self.search_edit); sr.addWidget(self.btn_search)
        right.addLayout(sr)

        self.tabs = QtWidgets.QTabWidget()
        right.addWidget(self.tabs)

        # Pair tab
        self.tab_pair = QtWidgets.QWidget()
        vpair = QtWidgets.QVBoxLayout(self.tab_pair)
        self.label_pair_stats = QtWidgets.QLabel("—")
        self.table_pair = QtWidgets.QTableWidget(0, 5)
        self.table_pair.setHorizontalHeaderLabels(["总重(每只, 不含杆, kg)", "每侧厚度(cm)", "方案（每侧）", "上片图预览", "一对含杆总重（公式）"])
        for i in (0,1,3,4):
            self.table_pair.horizontalHeader().setSectionResizeMode(i, QtWidgets.QHeaderView.ResizeToContents)
        self.table_pair.horizontalHeader().setSectionResizeMode(2, QtWidgets.QHeaderView.Stretch)
        self.btn_export_pair = QtWidgets.QPushButton("导出结果为 CSV（哑铃一对）")
        vpair.addWidget(self.label_pair_stats); vpair.addWidget(self.table_pair); vpair.addWidget(self.btn_export_pair)
        self.tabs.addTab(self.tab_pair, "哑铃（配成一对）")

        # Connector tab
        self.tab_conn = QtWidgets.QWidget()
        vconn = QtWidgets.QVBoxLayout(self.tab_conn)
        self.label_conn_stats = QtWidgets.QLabel("—")
        self.table_conn = QtWidgets.QTableWidget(0, 5)
        self.table_conn.setHorizontalHeaderLabels(["总重(整根, 不含杆, kg)", "每侧厚度(cm)", "方案（每侧）", "上片图预览", "含杆总重(kg)"])
        for i in (0,1,3,4):
            self.table_conn.horizontalHeader().setSectionResizeMode(i, QtWidgets.QHeaderView.ResizeToContents)
        self.table_conn.horizontalHeader().setSectionResizeMode(2, QtWidgets.QHeaderView.Stretch)
        self.btn_export_conn = QtWidgets.QPushButton("导出结果为 CSV（连接杆）")
        vconn.addWidget(self.label_conn_stats); vconn.addWidget(self.table_conn); vconn.addWidget(self.btn_export_conn)
        self.tabs.addTab(self.tab_conn, "连接杆（单根）")

        # Single dumbbell tab
        self.tab_single = QtWidgets.QWidget()
        vs = QtWidgets.QVBoxLayout(self.tab_single)
        self.label_single_stats = QtWidgets.QLabel("—")
        self.table_single = QtWidgets.QTableWidget(0, 5)
        self.table_single.setHorizontalHeaderLabels(["总重(单只, 不含杆, kg)", "每侧厚度(cm)", "方案（每侧）", "上片图预览", "含杆总重(kg)"])
        for i in (0,1,3,4):
            self.table_single.horizontalHeader().setSectionResizeMode(i, QtWidgets.QHeaderView.ResizeToContents)
        self.table_single.horizontalHeader().setSectionResizeMode(2, QtWidgets.QHeaderView.Stretch)
        self.btn_export_single = QtWidgets.QPushButton("导出结果为 CSV（单只哑铃）")
        vs.addWidget(self.label_single_stats); vs.addWidget(self.table_single); vs.addWidget(self.btn_export_single)
        self.tabs.addTab(self.tab_single, "单只哑铃")

        # Diagram
        self.canvas = PlateDiagramCanvas()
        right.addWidget(self.canvas)

        # Signals
        self.btn_add.clicked.connect(self.add_row)
        self.btn_del.clicked.connect(self.del_rows)
        self.btn_sample.clicked.connect(self.load_sample)
        self.btn_load.clicked.connect(self.open_json)
        self.btn_save.clicked.connect(self.save_json)
        self.btn_calc.clicked.connect(self.calculate)
        self.btn_export_pair.clicked.connect(lambda: self.export_csv("pair"))
        self.btn_export_conn.clicked.connect(lambda: self.export_csv("connector"))
        self.btn_export_single.clicked.connect(lambda: self.export_csv("single"))
        self.table_pair.itemSelectionChanged.connect(lambda: self.preview_diagram("pair"))
        self.table_conn.itemSelectionChanged.connect(lambda: self.preview_diagram("connector"))
        self.table_single.itemSelectionChanged.connect(lambda: self.preview_diagram("single"))
        self.btn_search.clicked.connect(self.search_weight)

        self.load_sample()

    # --- inventory helpers ---
    def add_row(self, weight=None, thickness=None, count=None, label=None):
        r = self.table.rowCount()
        self.table.insertRow(r)
        w = QtWidgets.QDoubleSpinBox(); w.setRange(0.0, 999.0); w.setDecimals(3); w.setValue(weight if weight is not None else 0.0)
        t = QtWidgets.QDoubleSpinBox(); t.setRange(0.0, 999.0); t.setDecimals(3); t.setValue(thickness if thickness is not None else 0.0)
        c = QtWidgets.QSpinBox(); c.setRange(0, 10000); c.setValue(count if count is not None else 0)
        l = QtWidgets.QLineEdit(label or "")
        self.table.setCellWidget(r, 0, w); self.table.setCellWidget(r, 1, t); self.table.setCellWidget(r, 2, c); self.table.setCellWidget(r, 3, l)

    def del_rows(self):
        rows = sorted({i.row() for i in self.table.selectedIndexes()}, reverse=True)
        for r in rows:
            self.table.removeRow(r)

    def load_sample(self):
        self.table.setRowCount(0)
        sample = [
            (3.0, 4.0, 10, "3 kg"),
            (2.5, 4.0, 2, "2.5 kg"),
            (2.0, 4.0, 4, "2 kg"),
            (1.5, 3.5, 2, "1.5 kg"),
            (1.25, 3.0, 10, "1.25 kg"),
        ]
        for w, t, c, l in sample:
            self.add_row(w, t, c, l)
        self.input_len_pair.setValue(21.0)
        self.input_len_conn.setValue(21.0)
        self.input_bar_pair.setValue(0.365)  # 默认
        self.input_bar_conn.setValue(1.0)    # 默认

    def open_json(self):
        path, _ = QtWidgets.QFileDialog.getOpenFileName(self, "打开清单 JSON", "", "JSON (*.json)")
        if not path:
            return
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        self.table.setRowCount(0)
        for item in data:
            self.add_row(item.get("weight",0.0), item.get("thickness",0.0), item.get("count",0), item.get("label",""))

    def save_json(self):
        path, _ = QtWidgets.QFileDialog.getSaveFileName(self, "保存清单为 JSON", "plates.json", "JSON (*.json)")
        if not path:
            return
        with open(path, "w", encoding="utf-8") as f:
            json.dump(self.collect_plates_dicts(), f, ensure_ascii=False, indent=2)

    def collect_plates(self) -> List[PlateType]:
        out: List[PlateType] = []
        for r in range(self.table.rowCount()):
            w = self.table.cellWidget(r, 0).value()
            t = self.table.cellWidget(r, 1).value()
            c = self.table.cellWidget(r, 2).value()
            l = self.table.cellWidget(r, 3).text().strip()
            if w>0 and t>0 and c>0:
                out.append(PlateType(weight=float(w), thickness=float(t), count=int(c), label=l))
        out.sort(key=lambda p: (-p.weight, -p.thickness))
        return out

    def collect_plates_dicts(self):
        out = []
        for r in range(self.table.rowCount()):
            w = self.table.cellWidget(r, 0).value()
            t = self.table.cellWidget(r, 1).value()
            c = self.table.cellWidget(r, 2).value()
            l = self.table.cellWidget(r, 3).text().strip()
            out.append({"weight": float(w), "thickness": float(t), "count": int(c), "label": l})
        return out

    # --- calculate & populate ---
    def calculate(self):
        plates = self.collect_plates()
        if not plates:
            QtWidgets.QMessageBox.warning(self, "提示", "请先输入有效的杠片清单。")
            return
        self.cached_plates = plates
        L_pair = float(self.input_len_pair.value())
        L_conn = float(self.input_len_conn.value())
        self.pair_results = enumerate_symmetric_combos(plates, L_pair, mode="pair")
        self.conn_results = enumerate_symmetric_combos(plates, L_conn, mode="connector")
        self.single_results = enumerate_symmetric_combos(plates, L_pair, mode="single")
        self.populate_result_table(self.table_pair, self.pair_results, "pair")
        self.populate_result_table(self.table_conn, self.conn_results, "connector")
        self.populate_result_table(self.table_single, self.single_results, "single")
        self.label_pair_stats.setText(f"总方案：{len(self.pair_results)}；不同重量：{len(set(r.total_weight for r in self.pair_results))}")
        self.label_conn_stats.setText(f"总方案：{len(self.conn_results)}；不同重量：{len(set(r.total_weight for r in self.conn_results))}")
        self.label_single_stats.setText(f"总方案：{len(self.single_results)}；不同重量：{len(set(r.total_weight for r in self.single_results))}")
        if self.pair_results:
            self.tabs.setCurrentWidget(self.tab_pair); self.select_first_row(self.table_pair)
        elif self.conn_results:
            self.tabs.setCurrentWidget(self.tab_conn); self.select_first_row(self.table_conn)
        elif self.single_results:
            self.tabs.setCurrentWidget(self.tab_single); self.select_first_row(self.table_single)

    def select_first_row(self, table):
        if table.rowCount()>0:
            table.setCurrentCell(0, 0)

    def _ro(self, text: str):
        it = QtWidgets.QTableWidgetItem(text)
        it.setFlags(it.flags() ^ QtCore.Qt.ItemIsEditable)
        return it

    def populate_result_table(self, table: QtWidgets.QTableWidget, results, mode: str):
        table.setRowCount(0)
        bar_pair = float(self.input_bar_pair.value())
        bar_conn = float(self.input_bar_conn.value())
        for r, res in enumerate(results):
            table.insertRow(r)
            if mode == "pair":
                # 每只不含杆 + 公式列
                table.setItem(r, 0, self._ro(fmt_num(res.total_weight)))
                table.setItem(r, 1, self._ro(fmt_num(res.per_side_thickness)))
                table.setItem(r, 2, self._ro(res.note))
                btn = QtWidgets.QPushButton("查看上片图")
                btn.clicked.connect(lambda _, rr=r, m=mode: self.render_row_diagram(m, rr))
                table.setCellWidget(r, 3, btn)
                pair_with_bars = res.total_weight*2.0 + bar_pair*2.0
                formula = f"{fmt_num(res.total_weight)}×2 + {fmt_num(bar_pair)}×2 = {fmt_num(pair_with_bars)}"
                table.setItem(r, 4, self._ro(formula))
            elif mode == "connector":
                # 不含杆 + 含杆
                table.setItem(r, 0, self._ro(fmt_num(res.total_weight)))
                table.setItem(r, 1, self._ro(fmt_num(res.per_side_thickness)))
                table.setItem(r, 2, self._ro(res.note))
                btn = QtWidgets.QPushButton("查看上片图")
                btn.clicked.connect(lambda _, rr=r, m=mode: self.render_row_diagram(m, rr))
                table.setCellWidget(r, 3, btn)
                with_bar = res.total_weight + bar_conn
                table.setItem(r, 4, self._ro(fmt_num(with_bar)))
            else:  # single
                # 单只：不含杆在前，含杆在最后
                with_bar = res.total_weight + bar_pair
                table.setItem(r, 0, self._ro(fmt_num(res.total_weight)))
                table.setItem(r, 1, self._ro(fmt_num(res.per_side_thickness)))
                table.setItem(r, 2, self._ro(res.note))
                btn = QtWidgets.QPushButton("查看上片图")
                btn.clicked.connect(lambda _, rr=r, m=mode: self.render_row_diagram(m, rr))
                table.setCellWidget(r, 3, btn)
                table.setItem(r, 4, self._ro(fmt_num(with_bar)))
        table.resizeRowsToContents()
        table.scrollToTop()

    # --- search ---
    def search_weight(self):
        t = self.search_edit.text().strip()
        if not t:
            return
        try:
            target = float(t)
        except ValueError:
            QtWidgets.QMessageBox.warning(self, "提示", "请输入数字（kg）。")
            return
        current = self.tabs.currentWidget()
        if current == self.tab_pair:
            table, col = self.table_pair, 4
        elif current == self.tab_conn:
            table, col = self.table_conn, 4
        else:
            table, col = self.table_single, 4  # 单只按“含杆总重”列搜索
        exact, near = [], []
        for r in range(table.rowCount()):
            try:
                w = float(table.item(r, col).text())
            except Exception:
                continue
            if abs(w - target) < 1e-9:
                exact.append(r)
            elif abs(w - target) <= 1.0 + 1e-9:
                near.append((abs(w - target), r))
        if exact:
            row = exact[0]
            table.setCurrentCell(row, col)
            table.scrollToItem(table.item(row, col), QtWidgets.QAbstractItemView.PositionAtCenter)
            QtWidgets.QMessageBox.information(self, "搜索结果", f"找到精确匹配：{target:g} kg。")
            return
        if near:
            near.sort()
            best = near[0][0]
            cands = [r for d, r in near if abs(d - best) < 1e-9]
            row = cands[0]
            table.setCurrentCell(row, col)
            table.scrollToItem(table.item(row, col), QtWidgets.QAbstractItemView.PositionAtCenter)
            weights = ", ".join([table.item(r, col).text() for r in cands[:5]])
            QtWidgets.QMessageBox.information(self, "搜索结果", f"未找到 {target:g} kg；最近的 ±1 kg：{weights}")
            return
        QtWidgets.QMessageBox.information(self, "搜索结果", f"未找到 {target:g} kg，且 ±1 kg 内也无可行方案。")

    # --- diagram preview & render ---
    def preview_diagram(self, mode: str):
        table = {"pair": self.table_pair, "connector": self.table_conn, "single": self.table_single}[mode]
        row = table.currentRow()
        if row < 0:
            return
        self.render_row_diagram(mode, row)

    def render_row_diagram(self, mode: str, row: int):
        plates = getattr(self, "cached_plates", self.collect_plates())
        if mode == "pair":
            results = getattr(self, "pair_results", [])
            side_len = float(self.input_len_pair.value())
        elif mode == "connector":
            results = getattr(self, "conn_results", [])
            side_len = float(self.input_len_conn.value())
        else:
            results = getattr(self, "single_results", [])
            side_len = float(self.input_len_pair.value())
        if not results or row < 0 or row >= len(results):
            return
        res = results[row]
        self.canvas.draw_layout(plates, res.per_side_counts, side_len)

def main():
    app = QtWidgets.QApplication([])
    w = MainWindow(); w.show()
    app.exec()

if __name__ == "__main__":
    main()
