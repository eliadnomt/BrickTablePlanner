from pathlib import Path

from baseplate import build_baseplate_grid
from context import SceneContext
from digits import build_centered_digit
from minifig import build_minifig
from plate import build_plate, build_plate_rotated
from template import load_template
from text import (
    build_text_from_top_left,
    build_text_vertical_from_top_left,
    measure_text,
)
from topologies import compute_layout


def add_section(lines, title):
    lines.append("0")
    lines.append(f"0 ===== {title} =====")
    lines.append("0")


def build_group_frame(ctx, center_stud_x, center_stud_z, color=15):
    lines = []

    width = 32
    height = 30

    left = center_stud_x - (width - 1) / 2
    right = left + (width - 1)
    bottom = center_stud_z - (height - 1) / 2
    top = bottom + (height - 1)

    # Top / bottom: 32 = 4 + 6 + 6 + 6 + 6 + 4
    horizontal_segments = [4, 6, 6, 6, 6, 4]
    for z_edge in (bottom, top):
        x_start = left
        for length in horizontal_segments:
            x_center = x_start + (length - 1) / 2
            lines.append(build_plate(ctx, x_center, z_edge, color, length))
            x_start += length

    # Left / right excluding corners: 28 = 6 + 6 + 6 + 6 + 4
    vertical_segments = [6, 6, 6, 6, 4]
    for x_edge in (left, right):
        z_start = bottom + 1
        for length in vertical_segments:
            z_center = z_start + (length - 1) / 2
            lines.append(build_plate_rotated(ctx, x_edge, z_center, color, length))
            z_start += length

    return lines


def build_group(ctx, template, digit, center_stud_x, center_stud_z, color=15):
    lines = []

    add_section(lines, f"GROUP {digit}")

    lines.append(f"0 -- Digit {digit} --")
    lines.extend(build_centered_digit(ctx, digit, center_stud_x, center_stud_z, color))

    lines.append("0 -- Minifigures --")

    # Explicit layout:
    # top:    4 minifigs
    # middle: 2 minifigs
    # bottom: 4 minifigs
    #
    # This avoids the broken spacing caused by a 4x3 grid with 2 removed cells.

    positions = [
        (-11, 11),
        (-4, 11),
        (4, 11),
        (11, 11),
        (-11, 0),
        (11, 0),
        (-11, -11),
        (-4, -11),
        (4, -11),
        (11, -11),
    ]

    for x_offset, z_offset in positions:
        fx = center_stud_x + x_offset
        fz = center_stud_z + z_offset
        lines.extend(build_minifig(ctx, template, stud_x=fx, stud_z=fz))

    lines.append("0 -- Frame --")
    lines.extend(build_group_frame(ctx, center_stud_x, center_stud_z))

    return lines


def build_table_groups(
    ctx, template, table_positions, grid_rows, studs_per_plate=32, color=15
):
    lines = []
    add_section(lines, "TABLE GROUPS")

    for digit, plate_row, plate_col in table_positions:
        row_from_bottom = (grid_rows - 1) - plate_row
        center_x = plate_col * studs_per_plate
        center_z = row_from_bottom * studs_per_plate

        lines.extend(build_group(ctx, template, digit, center_x, center_z, color))

    return lines


def build_text_on_baseplate(
    ctx,
    text,
    plate_row,
    plate_col,
    grid_rows,
    studs_per_plate=32,
    color=15,
    center=True,
    orientation="horizontal",
    letter_spacing=1,
    line_spacing=1,
    delta_x=0,
    delta_z=0,
):
    """
    Render text inside one logical baseplate cell.

    Important:
    - plate_col * studs_per_plate and row_from_bottom * studs_per_plate are the
      CENTER coordinates of the baseplate in this project.
    - Therefore we must first convert that center to the baseplate bounds in
      stud space before placing centered text.
    """

    row_from_bottom = (grid_rows - 1) - plate_row

    # Baseplate center in stud space
    center_x = plate_col * studs_per_plate
    center_z = row_from_bottom * studs_per_plate

    # Real usable baseplate bounds in stud space
    half_span = (studs_per_plate - 1) / 2
    left_x = center_x - half_span
    right_x = center_x + half_span
    bottom_z = center_z - half_span
    top_z = center_z + half_span

    width, height = measure_text(
        text,
        letter_spacing=letter_spacing,
        line_spacing=line_spacing,
        vertical=(orientation == "vertical"),
    )

    if center:
        start_x = left_x + (studs_per_plate - width) / 2
        start_z = top_z - (studs_per_plate - height) / 2
    else:
        start_x = left_x + 4
        start_z = top_z - 4

    start_x += delta_x
    start_z += delta_z

    if orientation == "vertical":
        return build_text_vertical_from_top_left(
            ctx,
            text,
            start_x,
            start_z,
            color=color,
            line_spacing=line_spacing,
        )

    return build_text_from_top_left(
        ctx,
        text,
        start_x,
        start_z,
        color=color,
        letter_spacing=letter_spacing,
    )


def build_names(
    ctx, partner1, partner2, name_positions, grid_rows, studs_per_plate=32, color=15
):
    lines = []

    for config in name_positions:
        text = partner1 if config["slot"] == "partner1" else partner2

        add_section(lines, f"NAME - {text}")

        lines.extend(
            build_text_on_baseplate(
                ctx,
                text,
                plate_row=config["plate_row"],
                plate_col=config["plate_col"],
                grid_rows=grid_rows,
                studs_per_plate=studs_per_plate,
                color=color,
                center=config.get("center", True),
                orientation=config.get("orientation", "horizontal"),
                delta_x=config.get("delta_x", 0),
                delta_z=config.get("delta_z", 0),
            )
        )

    return lines


def generate_model(
    partner1, partner2, guest_count, topology_key, output_path=None, template_path=None
):
    if guest_count <= 0 or guest_count % 10 != 0:
        raise ValueError("guest_count must be a positive multiple of 10")

    table_count = guest_count // 10
    layout = compute_layout(table_count, topology_key)

    project_dir = Path(__file__).parent

    if template_path is None:
        template_path = project_dir / "template" / "minifig.ldr"
    else:
        template_path = Path(template_path)

    if output_path is None:
        output_path = project_dir / "build" / "wedding_seating_chart.ldr"
    else:
        output_path = Path(output_path)

    output_path.parent.mkdir(parents=True, exist_ok=True)

    ctx = SceneContext(ground_y=0)

    lines = [
        "0 LEGO Wedding Seating Chart",
        f"0 Partner 1: {partner1}",
        f"0 Partner 2: {partner2}",
        f"0 Guests: {guest_count}",
        f"0 Topology: {topology_key}",
        "0",
    ]

    add_section(lines, "BASEPLATES")
    lines.extend(
        build_baseplate_grid(
            ctx,
            cols=layout["grid_cols"],
            rows=layout["grid_rows"],
            color=1,
        )
    )

    tpl = load_template(template_path)

    lines.extend(
        build_table_groups(
            ctx,
            tpl,
            table_positions=layout["table_positions"],
            grid_rows=layout["grid_rows"],
            color=15,
        )
    )

    lines.extend(
        build_names(
            ctx,
            partner1,
            partner2,
            name_positions=layout["name_positions"],
            grid_rows=layout["grid_rows"],
            color=15,
        )
    )

    output_path.write_text("\n".join(lines), encoding="utf-8")

    return {
        "output_path": str(output_path),
        "table_count": table_count,
        "grid_cols": layout["grid_cols"],
        "grid_rows": layout["grid_rows"],
        "table_positions": layout["table_positions"],
        "name_positions": layout["name_positions"],
        "lines": lines,
    }
