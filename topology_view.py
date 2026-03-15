from PySide6.QtCore import Qt, QRectF
from PySide6.QtGui import QColor, QBrush, QPen, QFont
from PySide6.QtWidgets import QWidget


class TopologyPreviewWidget(QWidget):
    """
    Simple topology preview widget.
    Draws groups and spouse-name positions as a schematic layout.
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self.group_positions = []
        self.name_positions = []
        self.setMinimumSize(420, 520)

    def set_layout_data(self, group_positions, name_positions):
        self.group_positions = group_positions
        self.name_positions = name_positions
        self.update()

    def paintEvent(self, event):
        from PySide6.QtGui import QPainter

        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.fillRect(self.rect(), QColor("#ffffff"))

        if not self.group_positions and not self.name_positions:
            painter.end()
            return

        all_points = []
        for item in self.group_positions:
            all_points.append((item["col"], item["row"]))
        for item in self.name_positions:
            all_points.append((item["col"], item["row"]))

        min_col = min(c for c, _ in all_points)
        max_col = max(c for c, _ in all_points)
        min_row = min(r for _, r in all_points)
        max_row = max(r for _, r in all_points)

        margin = 30
        cols = max_col - min_col + 1
        rows = max_row - min_row + 1

        available_w = self.width() - 2 * margin
        available_h = self.height() - 2 * margin

        cell_size = min(
            available_w / max(cols, 1),
            available_h / max(rows, 1),
        )

        def to_xy(col, row):
            x = margin + (col - min_col) * cell_size
            y = margin + (row - min_row) * cell_size
            return x, y

        painter.setPen(QPen(QColor("#888888"), 1))
        painter.setBrush(QBrush(QColor("#dbeafe")))

        for item in self.name_positions:
            x, y = to_xy(item["col"], item["row"])
            rect = QRectF(x + 6, y + 6, cell_size - 12, cell_size - 12)
            painter.drawRoundedRect(rect, 8, 8)

            painter.setPen(QColor("#1e3a8a"))
            painter.setFont(QFont("Arial", 10, QFont.Bold))
            painter.drawText(rect, Qt.AlignCenter, item["label"])
            painter.setPen(QPen(QColor("#888888"), 1))

        for item in self.group_positions:
            x, y = to_xy(item["col"], item["row"])
            rect = QRectF(x + 10, y + 10, cell_size - 20, cell_size - 20)

            painter.setPen(QPen(QColor("#444444"), 2))
            painter.setBrush(QBrush(QColor("#fde68a")))
            painter.drawRoundedRect(rect, 10, 10)

            painter.setPen(QColor("#92400e"))
            painter.setFont(QFont("Arial", 12, QFont.Bold))
            painter.drawText(rect, Qt.AlignCenter, str(item["label"]))

        painter.end()
