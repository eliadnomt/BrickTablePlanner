from PySide6.QtCore import Qt, QRectF
from PySide6.QtGui import QColor, QBrush, QPen, QFont, QFontMetricsF, QPainter
from PySide6.QtWidgets import QWidget


# Cells smaller than this (px, the limiting dimension) just show the table
# number; below that there is no room to draw guest names.
_MIN_CELL_FOR_NAMES = 62.0

# Padding inside each grid cell, around the table + name bands.
_CELL_PAD = 5.0


class TopologyPreviewWidget(QWidget):
    """
    Preview of the LEGO seating-chart layout.

    It always draws the grid defined by the chosen topology: numbered table
    cells in their grid positions plus the partner-name cells. When a guest list
    has been loaded, each table is drawn as a square (it represents a square LEGO
    baseplate) with its guests arranged around the four sides in seating order —
    so neighbours, including across a corner, are visible — colour-coded by
    spoken language. Every guest name is drawn at the same font size: the largest
    size at which the longest name still fits.
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self.group_positions = []   # [{"label": str, "row": int, "col": int}, ...]
        self.name_positions = []    # [{"label": str, "row": int, "col": int}, ...]
        # Seating overlay (aligned with group_positions by index): for table i,
        # tables_guests[i] is a list of (name, [languages]); None to skip.
        self.tables_guests = None
        self.language_colors = {}   # lower-cased language -> hex colour
        self.seats_per_table = 10
        self.setMinimumSize(560, 620)

    # --- public API --------------------------------------------------------
    def set_layout_data(self, group_positions, name_positions):
        self.group_positions = list(group_positions or [])
        self.name_positions = list(name_positions or [])
        self.tables_guests = None
        self.update()

    def set_seating_layout(self, group_positions, name_positions, tables_guests,
                           language_colors, seats_per_table=10):
        self.group_positions = list(group_positions or [])
        self.name_positions = list(name_positions or [])
        self.tables_guests = [list(t) for t in (tables_guests or [])]
        self.language_colors = dict(language_colors or {})
        self.seats_per_table = seats_per_table or 10
        self.update()

    def clear_seating(self):
        self.tables_guests = None
        self.update()

    # --- painting ----------------------------------------------------------
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.fillRect(self.rect(), QColor("#ffffff"))
        try:
            self._paint(painter)
        finally:
            painter.end()

    def _paint(self, painter):
        if not self.group_positions and not self.name_positions:
            painter.setPen(QColor("#6b7280"))
            painter.setFont(QFont("Arial", 11))
            painter.drawText(self.rect(), Qt.AlignCenter, "Nothing to preview yet.")
            return

        # Keep only grid rows/columns that are actually used, so a sparse layout
        # still gets large cells.
        used_cols = sorted({it["col"] for it in self.group_positions}
                           | {it["col"] for it in self.name_positions})
        used_rows = sorted({it["row"] for it in self.group_positions}
                           | {it["row"] for it in self.name_positions})
        col_index = {c: i for i, c in enumerate(used_cols)}
        row_index = {r: i for i, r in enumerate(used_rows)}

        margin = 14.0
        cell_w = (self.width() - 2 * margin) / max(len(used_cols), 1)
        cell_h = (self.height() - 2 * margin) / max(len(used_rows), 1)

        def cell_rect(col, row):
            return QRectF(margin + col_index[col] * cell_w,
                          margin + row_index[row] * cell_h, cell_w, cell_h)

        draw_guests = (
            self.tables_guests is not None
            and min(cell_w, cell_h) >= _MIN_CELL_FOR_NAMES
        )

        # One uniform guest-name font for the whole chart: the largest size at
        # which the longest name still fits the tightest label slot (which the
        # busiest table dictates).
        guest_font = None
        if draw_guests:
            populated = [t for t in self.tables_guests if t]
            if populated:
                n_max = max(len(t) for t in populated)
                longest = max((str(g[0]) for t in populated for g in t),
                              key=len, default="")
                max_langs = max((len(g[1] or []) for t in populated for g in t),
                                default=1)
                inner_sample = QRectF(0, 0, cell_w - 2 * _CELL_PAD, cell_h - 2 * _CELL_PAD)
                geo = self._table_geometry(inner_sample, n_max)
                tight_w, tight_h = self._tightest_label_box(geo)
                reserve = 9.0 * max_langs + 5.0
                guest_font = self._fit_font(longest, max(tight_w - reserve, 6.0), tight_h)

        # Partner-name cells.
        for item in self.name_positions:
            rect = cell_rect(item["col"], item["row"]).adjusted(8, 8, -8, -8)
            painter.setPen(QPen(QColor("#888888"), 1))
            painter.setBrush(QBrush(QColor("#dbeafe")))
            painter.drawRoundedRect(rect, 8, 8)
            painter.setPen(QColor("#1e3a8a"))
            label_text = str(item["label"])
            size = max(10, min(int(rect.height() * 0.22),
                               int(rect.width() * 0.82 / max(len(label_text), 1)), 18))
            painter.setFont(QFont("Arial", size, QFont.Bold))
            painter.drawText(rect, Qt.AlignCenter, label_text)

        # Table cells.
        for index, item in enumerate(self.group_positions):
            rect = cell_rect(item["col"], item["row"])
            guests = None
            if self.tables_guests is not None and index < len(self.tables_guests):
                guests = self.tables_guests[index]
            if draw_guests and guests is not None:
                self._paint_table_with_guests(painter, rect, str(item["label"]),
                                               guests, guest_font)
            else:
                self._paint_plain_table(painter, rect, str(item["label"]),
                                        len(guests) if guests is not None else None)

    # --- geometry ----------------------------------------------------------
    @staticmethod
    def _side_counts(n):
        """Distribute n seats around the four sides -> (top, right, bottom, left).

        As even as possible; the remainder goes to top, bottom, right, left in
        that order so the wide top/bottom rows take any extras.
        """
        if n <= 0:
            return 0, 0, 0, 0
        base, rem = divmod(n, 4)
        top = bottom = right = left = base
        for who in range(rem):
            if who == 0:
                top += 1
            elif who == 1:
                bottom += 1
            elif who == 2:
                right += 1
            else:
                left += 1
        return top, right, bottom, left

    @staticmethod
    def _table_geometry(inner, n):
        top_n, right_n, bottom_n, left_n = TopologyPreviewWidget._side_counts(n)
        # A square table (it represents a square baseplate), centred in the cell.
        # Reserve name bands on every side: vertical bands (a row of names) above
        # and below, horizontal bands (a column of names) left and right. The
        # square table fills whatever is left, so it is as large as the cell
        # allows while still leaving room to space the names out.
        band_v = max(15.0, inner.height() * 0.17)
        band_h = max(18.0, inner.width() * 0.22)
        avail_w = max(inner.width() - 2.0 * band_h, 24.0)
        avail_h = max(inner.height() - 2.0 * band_v, 24.0)
        side = max(28.0, min(avail_w, avail_h))
        table_rect = QRectF(
            inner.x() + (inner.width() - side) / 2,
            inner.y() + (inner.height() - side) / 2,
            side, side,
        )
        return {
            "top_n": top_n, "right_n": right_n, "bottom_n": bottom_n, "left_n": left_n,
            "table": table_rect,
            "top_band": table_rect.y() - inner.y(),
            "bottom_band": inner.bottom() - table_rect.bottom(),
            "left_band": table_rect.x() - inner.x(),
            "right_band": inner.right() - table_rect.right(),
            "slot_w_top": inner.width() / max(top_n, 1),
            "slot_w_bottom": inner.width() / max(bottom_n, 1),
            "slot_h_left": side / max(left_n, 1),
            "slot_h_right": side / max(right_n, 1),
        }

    @staticmethod
    def _tightest_label_box(geo):
        widths, heights = [], []
        if geo["top_n"]:
            widths.append(geo["slot_w_top"]); heights.append(geo["top_band"])
        if geo["bottom_n"]:
            widths.append(geo["slot_w_bottom"]); heights.append(geo["bottom_band"])
        if geo["left_n"]:
            widths.append(geo["left_band"]); heights.append(geo["slot_h_left"])
        if geo["right_n"]:
            widths.append(geo["right_band"]); heights.append(geo["slot_h_right"])
        return (min(widths) if widths else 1e9, min(heights) if heights else 1e9)

    # --- table renderers ---------------------------------------------------
    def _color_for_language(self, language):
        return QColor(self.language_colors.get((language or "").lower(), "#374151"))

    def _paint_plain_table(self, painter, cell, label, guest_count):
        side = max(20.0, min(cell.width(), cell.height()) * 0.62)
        rect = QRectF(cell.x() + (cell.width() - side) / 2,
                      cell.y() + (cell.height() - side) / 2, side, side)
        painter.setPen(QPen(QColor("#444444"), 2))
        painter.setBrush(QBrush(QColor("#fde68a")))
        painter.drawRoundedRect(rect, 8, 8)
        painter.setPen(QColor("#92400e"))
        painter.setFont(QFont("Arial", max(8, int(side * 0.16)), QFont.Bold))
        text = label if guest_count is None else f"{label}\n({guest_count})"
        painter.drawText(rect, Qt.AlignCenter, text)

    def _paint_table_with_guests(self, painter, cell, label, guests, font):
        n = len(guests)
        inner = cell.adjusted(_CELL_PAD, _CELL_PAD, -_CELL_PAD, -_CELL_PAD)
        geo = self._table_geometry(inner, n)
        table_rect = geo["table"]

        if font is None:
            font = QFont("Arial", 8)
        fm = QFontMetricsF(font)
        dot = min(max(3.5, fm.height() * 0.5), 8.0)

        # The square table (a square baseplate).
        painter.setPen(QPen(QColor("#b45309"), 2))
        painter.setBrush(QBrush(QColor("#fde68a")))
        painter.drawRoundedRect(table_rect, 8, 8)
        painter.setPen(QColor("#92400e"))
        painter.setFont(QFont("Arial", max(8, int(table_rect.height() * 0.13)), QFont.Bold))
        painter.drawText(table_rect, Qt.AlignCenter, f"Table {label}\n{n}")
        painter.setFont(font)

        # Walk the perimeter clockwise so consecutive guests are neighbours:
        # top left->right, right top->bottom, bottom right->left, left bottom->top.
        seat = 0
        for k in range(geo["top_n"]):
            box = QRectF(inner.x() + k * geo["slot_w_top"], inner.y(),
                         geo["slot_w_top"], geo["top_band"])
            self._draw_seat_label(painter, fm, dot, box, guests[seat], "center")
            seat += 1
        for k in range(geo["right_n"]):
            box = QRectF(table_rect.right() + 3, table_rect.y() + k * geo["slot_h_right"],
                         geo["right_band"] - 3, geo["slot_h_right"])
            self._draw_seat_label(painter, fm, dot, box, guests[seat], "left")
            seat += 1
        for k in range(geo["bottom_n"]):
            box = QRectF(inner.right() - (k + 1) * geo["slot_w_bottom"], table_rect.bottom(),
                         geo["slot_w_bottom"], geo["bottom_band"])
            self._draw_seat_label(painter, fm, dot, box, guests[seat], "center")
            seat += 1
        for k in range(geo["left_n"]):
            box = QRectF(inner.x(), table_rect.bottom() - (k + 1) * geo["slot_h_left"],
                         geo["left_band"] - 3, geo["slot_h_left"])
            self._draw_seat_label(painter, fm, dot, box, guests[seat], "right")
            seat += 1

    def _draw_seat_label(self, painter, fm, dot, box, guest, align="center"):
        name, languages = str(guest[0]), list(guest[1] or [])
        gap = 3.0
        swatch_w = ((dot + 1.5) * len(languages) + gap) if languages else 0.0
        total_w = swatch_w + fm.horizontalAdvance(name)
        if align == "right":
            start_x = box.right() - total_w
        elif align == "left":
            start_x = box.x()
        else:
            start_x = box.x() + (box.width() - total_w) / 2
        cy = box.y() + box.height() / 2

        x = start_x
        for lang in languages:
            painter.setPen(QPen(QColor("#9ca3af"), 0.5))
            painter.setBrush(QBrush(self._color_for_language(lang)))
            painter.drawRect(QRectF(x, cy - dot / 2, dot, dot))
            x += dot + 1.5
        if languages:
            x += gap

        painter.setPen(self._color_for_language(languages[0]) if len(languages) == 1
                       else QColor("#1f2937"))
        painter.drawText(QRectF(x, box.y(), box.right() - x + 30.0, box.height()),
                         Qt.AlignVCenter | Qt.AlignLeft, name)

    @staticmethod
    def _fit_font(text, max_w, max_h, max_pt=13, min_pt=5):
        for size in range(int(max_pt), int(min_pt) - 1, -1):
            fm = QFontMetricsF(QFont("Arial", size))
            if fm.horizontalAdvance(text) <= max_w and fm.height() <= max_h:
                return QFont("Arial", size)
        return QFont("Arial", int(min_pt))
