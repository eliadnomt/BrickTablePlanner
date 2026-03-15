TOPOLOGIES = {
    "two_columns_center_names": "Two columns / names in center",
    "three_columns_bottom_names": "Three columns / names below",
}


def get_topology_label(topology_key):
    return TOPOLOGIES[topology_key]


def get_topology_names():
    return list(TOPOLOGIES.keys())


def compute_layout(table_count, topology_key):
    """
    Compute the logical layout for the requested topology.

    Output:
    {
        "grid_cols": int,
        "grid_rows": int,
        "table_positions": [(digit, plate_row, plate_col), ...],
        "name_positions": [
            {
                "slot": "partner1" | "partner2",
                "plate_row": int,
                "plate_col": int,
                "center": bool,
                "orientation": "horizontal" | "vertical",
                "delta_x": int,
                "delta_z": int,
            },
            ...
        ],
    }

    Coordinate convention:
    - plate_row: 0 = TOP row
    - plate_col: 0 = LEFT column
    """

    if table_count <= 0:
        raise ValueError("table_count must be positive")

    if topology_key == "two_columns_center_names":
        if table_count > 10:
            raise ValueError("two_columns_center_names supports up to 10 tables")

        # Layout:
        # 1   6
        # 2   7
        # 3   8
        # 4   9
        # 5  10
        #
        # Names are on the CENTER column (plate_col = 1).
        grid_cols = 3
        grid_rows = 5

        left_count = min(5, table_count)
        right_count = max(0, table_count - 5)

        table_positions = []

        for i in range(left_count):
            digit = str(i + 1)
            table_positions.append((digit, i, 0))

        for i in range(right_count):
            digit = str(6 + i)
            table_positions.append((digit, i, 2))

        name_positions = [
            {
                "slot": "partner1",
                "plate_row": 2,
                "plate_col": 1,
                "center": True,
                "orientation": "vertical",
                "delta_x": -6,
                "delta_z": 0,
            },
            {
                "slot": "partner2",
                "plate_row": 3,
                "plate_col": 1,
                "center": True,
                "orientation": "vertical",
                "delta_x": 6,
                "delta_z": 0,
            },
        ]

        return {
            "grid_cols": grid_cols,
            "grid_rows": grid_rows,
            "table_positions": table_positions,
            "name_positions": name_positions,
        }

    if topology_key == "three_columns_bottom_names":
        # 3 columns of tables, names centered on the bottom row.
        grid_cols = 3
        table_rows = (table_count + grid_cols - 1) // grid_cols
        grid_rows = table_rows + 1  # extra row for names below

        table_positions = []

        for i in range(table_count):
            digit = str(i + 1)
            plate_row = i // grid_cols
            plate_col = i % grid_cols
            table_positions.append((digit, plate_row, plate_col))

        bottom_row = grid_rows - 1

        name_positions = [
            {
                "slot": "partner1",
                "plate_row": bottom_row,
                "plate_col": 0,
                "center": True,
                "orientation": "horizontal",
                "delta_x": 0,
                "delta_z": 0,
            },
            {
                "slot": "partner2",
                "plate_row": bottom_row,
                "plate_col": 2,
                "center": True,
                "orientation": "horizontal",
                "delta_x": 0,
                "delta_z": 0,
            },
        ]

        return {
            "grid_cols": grid_cols,
            "grid_rows": grid_rows,
            "table_positions": table_positions,
            "name_positions": name_positions,
        }

    raise ValueError(f"Unknown topology: {topology_key}")


def get_topology_preview(name, guest_count, spouse1, spouse2):
    """
    Return lightweight preview data for the UI.

    Output:
    {
        "groups": [{"label": "1", "row": 0, "col": 0}, ...],
        "names": [{"label": spouse1, "row": 3, "col": 2}, ...],
    }
    """

    tables = guest_count // 10
    layout = compute_layout(tables, name)

    groups = [
        {"label": digit, "row": plate_row, "col": plate_col}
        for digit, plate_row, plate_col in layout["table_positions"]
    ]

    names = []
    for item in layout["name_positions"]:
        label = spouse1 if item["slot"] == "partner1" else spouse2
        names.append(
            {
                "label": label,
                "row": item["plate_row"],
                "col": item["plate_col"],
            }
        )

    return {
        "groups": groups,
        "names": names,
    }
