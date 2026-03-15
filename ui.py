import signal
import sys
from PySide6.QtWidgets import (
    QMainWindow,
    QWidget,
    QLineEdit,
    QSpinBox,
    QComboBox,
    QPushButton,
    QTextEdit,
    QVBoxLayout,
    QFormLayout,
    QApplication,
    QMessageBox,
    QSplitter,
)
from PySide6.QtCore import Qt, QTimer

from bom import generate_bom_from_lines, format_bom_text
from generator import generate_model
from topologies import (
    get_topology_label,
    get_topology_names,
    get_topology_preview,
)
from topology_view import TopologyPreviewWidget


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("LEGO Wedding Seating Chart")

        self.spouse1_edit = QLineEdit("SOPHIE")
        self.spouse2_edit = QLineEdit("LAURENT")

        self.guests_spin = QSpinBox()
        self.guests_spin.setMinimum(10)
        self.guests_spin.setMaximum(500)
        self.guests_spin.setSingleStep(10)
        self.guests_spin.setValue(100)

        self.topology_combo = QComboBox()
        for name in get_topology_names():
            self.topology_combo.addItem(get_topology_label(name), name)

        self.generate_button = QPushButton("Generate")

        form_layout = QFormLayout()
        form_layout.addRow("Spouse 1", self.spouse1_edit)
        form_layout.addRow("Spouse 2", self.spouse2_edit)
        form_layout.addRow("Guests", self.guests_spin)
        form_layout.addRow("Topology", self.topology_combo)

        left_panel = QWidget()
        left_layout = QVBoxLayout(left_panel)
        left_layout.addLayout(form_layout)
        left_layout.addWidget(self.generate_button)
        left_layout.addStretch()

        self.preview_widget = TopologyPreviewWidget()

        self.bom_text = QTextEdit()
        self.bom_text.setReadOnly(True)

        right_splitter = QSplitter(Qt.Vertical)
        right_splitter.addWidget(self.preview_widget)
        right_splitter.addWidget(self.bom_text)
        right_splitter.setSizes([320, 260])

        main_splitter = QSplitter(Qt.Horizontal)
        main_splitter.addWidget(left_panel)
        main_splitter.addWidget(right_splitter)
        main_splitter.setSizes([260, 700])

        container = QWidget()
        root_layout = QVBoxLayout(container)
        root_layout.addWidget(main_splitter)
        self.setCentralWidget(container)

        self.topology_combo.currentIndexChanged.connect(self.refresh_preview)
        self.guests_spin.valueChanged.connect(self.refresh_preview)
        self.spouse1_edit.textChanged.connect(self.refresh_preview)
        self.spouse2_edit.textChanged.connect(self.refresh_preview)
        self.generate_button.clicked.connect(self.generate_project)

        self.refresh_preview()

    def current_topology(self):
        return self.topology_combo.currentData()

    def refresh_preview(self):
        topology_name = self.current_topology()
        guest_count = self.guests_spin.value()
        spouse1 = self.spouse1_edit.text().strip() or "SPOUSE 1"
        spouse2 = self.spouse2_edit.text().strip() or "SPOUSE 2"

        preview = get_topology_preview(
            topology_name,
            guest_count,
            spouse1,
            spouse2,
        )

        self.preview_widget.set_layout_data(
            preview["groups"],
            preview["names"],
        )

    def generate_project(self):
        try:
            result = generate_model(
                partner1=self.spouse1_edit.text().strip() or "PARTNER1",
                partner2=self.spouse2_edit.text().strip() or "PARTNER2",
                guest_count=self.guests_spin.value(),
                topology_key=self.current_topology(),
            )
        except Exception as exc:
            QMessageBox.critical(self, "Generation error", str(exc))
            return

        bom = generate_bom_from_lines(result["lines"])
        self.bom_text.setPlainText(format_bom_text(bom))

        QMessageBox.information(
            self,
            "Success",
            f"LDraw file generated:\n{result['output_path']}",
        )


def main():
    app = QApplication(sys.argv)
    window = MainWindow()
    window.resize(1100, 700)
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
