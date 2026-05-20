import math
import signal
import sys

from PySide6.QtWidgets import (
    QMainWindow,
    QWidget,
    QLabel,
    QLineEdit,
    QSpinBox,
    QComboBox,
    QPushButton,
    QTextEdit,
    QVBoxLayout,
    QHBoxLayout,
    QFormLayout,
    QApplication,
    QFileDialog,
    QMessageBox,
    QSplitter,
)
from PySide6.QtCore import Qt, QTimer

from bom import generate_bom_from_lines, format_bom_text
from generator import generate_model
from guests import GuestListError, load_guest_list
from seating import optimize_seating
from topologies import (
    compute_layout,
    get_topology_label,
    get_topology_max_tables,
    get_topology_names,
    get_topology_preview,
)
from topology_view import TopologyPreviewWidget


# Palette used to colour-code spoken languages (cycled if there are more
# languages than colours).
LANGUAGE_PALETTE = [
    "#2563eb",  # blue
    "#dc2626",  # red
    "#16a34a",  # green
    "#9333ea",  # purple
    "#ea580c",  # orange
    "#0891b2",  # teal
    "#ca8a04",  # gold
    "#db2777",  # pink
    "#4d7c0f",  # olive
    "#475569",  # slate
]


_HEADER_CELL = (
    "<th style='background:#1f2937; color:#ffffff; padding:4px;'>{}</th>"
)
_CELL = "<td style='padding:4px;'>{}</td>"

GUEST_LIST_FORMAT_HTML = (
    "<p style='margin:0 0 4px 0;'>A <b>.csv</b> or <b>.xlsx</b> file with a "
    "header row and these columns:</p>"
    "<table border='1' cellspacing='0' style='border-collapse:collapse; font-size:11px;'>"
    "<tr>"
    + _HEADER_CELL.format("first_name") + _HEADER_CELL.format("languages")
    + _HEADER_CELL.format("related_guests") + "</tr>"
    "<tr>" + _CELL.format("Sophie") + _CELL.format("French;English")
    + _CELL.format("Laurent;Marie") + "</tr>"
    "<tr>" + _CELL.format("Laurent") + _CELL.format("French")
    + _CELL.format("Sophie") + "</tr>"
    "<tr>" + _CELL.format("Pierre") + _CELL.format("French")
    + _CELL.format("<i>(empty)</i>") + "</tr>"
    "</table>"
    "<p style='margin:4px 0 0 0; color:#6b7280; font-size:11px;'>"
    "Names must be unique. List languages and related guests separated by "
    "<code>;</code> or <code>,</code>. <code>related_guests</code> may be empty; "
    "names listed there must appear in the <code>first_name</code> column, and a "
    "relationship only forces two guests together when <i>both</i> list each other."
    "</p>"
)


def assign_language_colors(guests):
    """Map each distinct (lower-cased) language to a stable colour."""
    seen = []
    for guest in guests:
        for language in guest.languages:
            key = language.lower()
            if key not in seen:
                seen.append(key)
    return {key: LANGUAGE_PALETTE[i % len(LANGUAGE_PALETTE)] for i, key in enumerate(seen)}


def _language_display_names(guests):
    display = {}
    for guest in guests:
        for language in guest.languages:
            display.setdefault(language.lower(), language)
    return display


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("LEGO Wedding Seating Chart")

        # Guest-list state.
        self.guests = None
        self.guest_list_path = None
        self.seating = None
        self.language_colors = {}

        self.spouse1_edit = QLineEdit("SOPHIE")
        self.spouse2_edit = QLineEdit("LAURENT")

        self.guests_spin = QSpinBox()
        self.guests_spin.setMinimum(10)
        self.guests_spin.setMaximum(10000)
        self.guests_spin.setSingleStep(10)
        self.guests_spin.setValue(100)

        self.topology_combo = QComboBox()
        for name in get_topology_names():
            self.topology_combo.addItem(get_topology_label(name), name)

        self.load_guests_button = QPushButton("Load guest list (.csv / .xlsx)…")
        self.clear_guests_button = QPushButton("Clear guest list")
        self.clear_guests_button.setEnabled(False)
        self.load_guests_button.setToolTip(GUEST_LIST_FORMAT_HTML)

        self.guest_status_label = QLabel("No guest list loaded.")
        self.guest_status_label.setWordWrap(True)

        self.format_label = QLabel(GUEST_LIST_FORMAT_HTML)
        self.format_label.setTextFormat(Qt.RichText)
        self.format_label.setWordWrap(True)

        self.legend_label = QLabel("")
        self.legend_label.setWordWrap(True)
        self.legend_label.setTextFormat(Qt.RichText)

        self.generate_button = QPushButton("Generate")

        form_layout = QFormLayout()
        form_layout.addRow("Spouse 1", self.spouse1_edit)
        form_layout.addRow("Spouse 2", self.spouse2_edit)
        form_layout.addRow("Guests", self.guests_spin)
        form_layout.addRow("Topology", self.topology_combo)

        guest_buttons = QHBoxLayout()
        guest_buttons.addWidget(self.load_guests_button)
        guest_buttons.addWidget(self.clear_guests_button)

        left_panel = QWidget()
        left_layout = QVBoxLayout(left_panel)
        left_layout.addLayout(form_layout)
        left_layout.addLayout(guest_buttons)
        left_layout.addWidget(self.guest_status_label)
        left_layout.addWidget(QLabel("<b>Guest list format</b>"))
        left_layout.addWidget(self.format_label)
        left_layout.addWidget(QLabel("<b>Language colours</b>"))
        left_layout.addWidget(self.legend_label)
        left_layout.addWidget(self.generate_button)
        left_layout.addStretch()

        self.preview_widget = TopologyPreviewWidget()

        self.bom_text = QTextEdit()
        self.bom_text.setReadOnly(True)

        right_splitter = QSplitter(Qt.Vertical)
        right_splitter.addWidget(self.preview_widget)
        right_splitter.addWidget(self.bom_text)
        right_splitter.setSizes([560, 200])

        main_splitter = QSplitter(Qt.Horizontal)
        main_splitter.addWidget(left_panel)
        main_splitter.addWidget(right_splitter)
        main_splitter.setSizes([340, 760])

        container = QWidget()
        root_layout = QVBoxLayout(container)
        root_layout.addWidget(main_splitter)
        self.setCentralWidget(container)

        self.topology_combo.currentIndexChanged.connect(self.refresh_preview)
        self.guests_spin.valueChanged.connect(self.refresh_preview)
        self.spouse1_edit.textChanged.connect(self.refresh_preview)
        self.spouse2_edit.textChanged.connect(self.refresh_preview)
        self.load_guests_button.clicked.connect(self.load_guest_list_dialog)
        self.clear_guests_button.clicked.connect(self.clear_guest_list)
        self.generate_button.clicked.connect(self.generate_project)

        self._update_legend()
        self.refresh_preview()

    # --- helpers -----------------------------------------------------------
    def current_topology(self):
        return self.topology_combo.currentData()

    def _spouse_names(self):
        return (
            self.spouse1_edit.text().strip() or "SPOUSE 1",
            self.spouse2_edit.text().strip() or "SPOUSE 2",
        )

    def _update_legend(self):
        if not self.guests:
            self.legend_label.setText("<i>(load a guest list to see languages)</i>")
            return
        display = _language_display_names(self.guests)
        chips = []
        for key, color in self.language_colors.items():
            label = display.get(key, key)
            chips.append(f'<span style="color:{color};">&#9608;</span>&nbsp;{label}')
        self.legend_label.setText("&nbsp;&nbsp;&nbsp;".join(chips) if chips else "")

    def _recompute_seating(self):
        if not self.guests:
            self.seating = None
            return None
        max_tables = get_topology_max_tables(self.current_topology())
        self.seating = optimize_seating(self.guests, max_tables=max_tables)
        return self.seating

    def _set_guest_count_display(self, value):
        """Show `value` in the (disabled) guests spin without firing signals."""
        self.guests_spin.blockSignals(True)
        if value < self.guests_spin.minimum():
            self.guests_spin.setMinimum(1)
        self.guests_spin.setValue(value)
        self.guests_spin.blockSignals(False)

    @staticmethod
    def _fallback_grid_positions(table_count):
        """A simple square grid of numbered tables, for when the chosen topology
        cannot represent that many tables."""
        n = max(table_count, 1)
        cols = min(5, max(1, math.ceil(math.sqrt(n))))
        return [
            {"label": str(i + 1), "row": i // cols, "col": i % cols}
            for i in range(n)
        ]

    def _seating_layout_positions(self, table_count):
        """Return (group_positions, name_positions) for `table_count` tables in
        the current topology, falling back to a simple square grid if the
        topology cannot hold that many."""
        spouse1, spouse2 = self._spouse_names()
        try:
            layout = compute_layout(table_count, self.current_topology())
            groups = [
                {"label": str(digit), "row": plate_row, "col": plate_col}
                for digit, plate_row, plate_col in layout["table_positions"]
            ]
            names = []
            for item in layout["name_positions"]:
                label = spouse1 if item["slot"] == "partner1" else spouse2
                names.append({"label": label, "row": item["plate_row"], "col": item["plate_col"]})
            return groups, names
        except ValueError:
            return self._fallback_grid_positions(table_count), []

    def _tables_guests(self):
        if not self.seating:
            return []
        return [
            [(g.name, list(g.languages)) for g in table]
            for table in self.seating.tables
        ]

    # --- guest list actions ------------------------------------------------
    def load_guest_list_dialog(self):
        path, _ = QFileDialog.getOpenFileName(
            self,
            "Select guest list",
            "",
            "Guest lists (*.csv *.xlsx);;CSV files (*.csv);;Excel files (*.xlsx);;All files (*)",
        )
        if not path:
            return

        try:
            guests = load_guest_list(path)
        except GuestListError as exc:
            QMessageBox.critical(self, "Could not load guest list", str(exc))
            return
        except Exception as exc:  # pragma: no cover - defensive
            QMessageBox.critical(self, "Could not load guest list", str(exc))
            return

        self.guests = guests
        self.guest_list_path = path
        self.language_colors = assign_language_colors(guests)
        self.clear_guests_button.setEnabled(True)
        self.guests_spin.setEnabled(False)

        self._update_legend()
        self.refresh_preview()

        table_count = max(self.seating.table_count, 1) if self.seating else 1
        self.guest_status_label.setText(
            f"Loaded {len(guests)} guests from “{path}” → {table_count} table(s) "
            f"(model rounds up to {table_count * 10} seats)."
        )

        if self.seating and not self.seating.feasible:
            self._show_violations_dialog(self.seating.violations)

    def clear_guest_list(self):
        self.guests = None
        self.guest_list_path = None
        self.seating = None
        self.language_colors = {}
        self.clear_guests_button.setEnabled(False)
        self.guests_spin.setEnabled(True)
        self.guests_spin.blockSignals(True)
        self.guests_spin.setMinimum(10)
        self.guests_spin.setValue(100)
        self.guests_spin.blockSignals(False)
        self.guest_status_label.setText("No guest list loaded.")
        self._update_legend()
        self.refresh_preview()

    def _show_violations_dialog(self, violations):
        box = QMessageBox(self)
        box.setIcon(QMessageBox.Warning)
        box.setWindowTitle("Seating constraints not satisfied")
        box.setText(
            "Some guests cannot be seated according to the constraints "
            "(related guests together / shared language with both neighbours)."
        )
        box.setInformativeText(
            "The following placements violate a constraint:\n\n"
            + "\n".join(f"• {v}" for v in violations)
        )
        box.exec()

    # --- preview -----------------------------------------------------------
    def refresh_preview(self):
        if self.guests:
            self._recompute_seating()
            table_count = max(self.seating.table_count, 1) if self.seating else 1
            self._set_guest_count_display(len(self.guests))
            groups, names = self._seating_layout_positions(table_count)
            self.preview_widget.set_seating_layout(
                groups,
                names,
                self._tables_guests(),
                self.language_colors,
                self.seating.seats_per_table if self.seating else 10,
            )
            return

        spouse1, spouse2 = self._spouse_names()
        try:
            preview = get_topology_preview(
                self.current_topology(),
                self.guests_spin.value(),
                spouse1,
                spouse2,
            )
            self.preview_widget.set_layout_data(preview["groups"], preview["names"])
        except ValueError:
            # The chosen topology cannot represent this many tables (e.g. the
            # two-column layout caps at 10 tables / 100 guests). Fall back to a
            # plain numbered grid so the preview still shows something useful.
            table_count = max(self.guests_spin.value() // 10, 1)
            self.preview_widget.set_layout_data(
                self._fallback_grid_positions(table_count), []
            )

    # --- generation --------------------------------------------------------
    def generate_project(self):
        if self.guests:
            self._recompute_seating()
            if self.seating and not self.seating.feasible:
                self._show_violations_dialog(self.seating.violations)
                return
            table_count = max(self.seating.table_count, 1) if self.seating else 1
            guest_count = table_count * 10
        else:
            guest_count = self.guests_spin.value()

        try:
            result = generate_model(
                partner1=self.spouse1_edit.text().strip() or "PARTNER1",
                partner2=self.spouse2_edit.text().strip() or "PARTNER2",
                guest_count=guest_count,
                topology_key=self.current_topology(),
            )
        except Exception as exc:
            QMessageBox.critical(self, "Generation error", str(exc))
            return

        bom = generate_bom_from_lines(result["lines"])
        self.bom_text.setPlainText(format_bom_text(bom))

        if self.guests and self.seating:
            plan = "\n".join(
                f"Table {i}: " + ", ".join(g.name for g in table)
                for i, table in enumerate(self.seating.tables, start=1)
            )
            QMessageBox.information(
                self,
                "Success",
                f"LDraw file generated:\n{result['output_path']}\n\n"
                f"Optimised seating:\n{plan}",
            )
        else:
            QMessageBox.information(
                self,
                "Success",
                f"LDraw file generated:\n{result['output_path']}",
            )


def main():
    app = QApplication(sys.argv)
    window = MainWindow()
    window.resize(1280, 880)
    window.show()

    # Allow Ctrl+C to terminate the Qt event loop cleanly.
    signal.signal(signal.SIGINT, lambda *_: app.quit())

    # Keep Python responsive to signals while Qt runs.
    timer = QTimer()
    timer.start(200)
    timer.timeout.connect(lambda: None)

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
