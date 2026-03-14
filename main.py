"""main.py

Generate an LDraw model:
  - a 3x4 baseplate grid (12 baseplates)
  - a single centered digit "0" (as 1x1 plates)
  - the minifig template (optional)

Open the generated .ldr file in BrickLink Studio to preview.
"""

from pathlib import Path

from baseplate import build_baseplate_grid
from bom import generate_bom_from_lines, print_bom, print_global_summary
from context import SceneContext
from digits import build_centered_digit
from minifig import build_minifig
from plate import build_plate, build_plate_rotated
from template import load_template, normalize_template_inplace
from text import build_text_from_top_left, LETTERS_5x7


def add_section(lines, title):
    lines.append("0")
    lines.append(f"0 ===== {title} =====")
    lines.append("0")


def build_group_frame(ctx, center_stud_x, center_stud_z, color=15):
    """
    Build a 1-stud thick rectangular frame (1xN plates).

    Dimensions:
        width  = 32 studs
        height = 30 studs

    Rules:
        - Horizontal bars include corners
        - Vertical bars exclude corners (no overlap)
        - LDraw coordinates represent the CENTER of the plate
    """

    lines = []

    width = 32
    height = 30

    # Proper stud-aligned rectangle
    left = center_stud_x - (width - 1) / 2
    right = left + (width - 1)

    bottom = center_stud_z - (height - 1) / 2
    top = bottom + (height - 1)

    # -------------------------
    # TOP & BOTTOM (32 = 4 + 6 + 6 + 6 + 6 + 4)
    # -------------------------
    horizontal_segments = [4, 6, 6, 6, 6, 4]

    for z_edge in (bottom, top):
        x_start = left

        for length in horizontal_segments:
            x_center = x_start + (length - 1) / 2
            lines.append(build_plate(ctx, x_center, z_edge, color, length))
            x_start += length

    # --------------------------------
    # LEFT & RIGHT (30 - 2 = 28 = 6 + 6 + 6 + 6 + 4)
    # --------------------------------
    vertical_segments = [6, 6, 6, 6, 4]

    for x_edge in (left, right):
        z_start = bottom + 1  # exclude bottom corner

        for length in vertical_segments:
            z_center = z_start + (length - 1) / 2
            lines.append(build_plate_rotated(ctx, x_edge, z_center, color, length))
            z_start += length

    return lines


def build_group(ctx, template, digit, center_stud_x, center_stud_z, color=15):

    lines = []

    add_section(lines, f"GROUP {digit}")

    lines.append(f"0 -- Digit {digit} --")

    lines.extend(
        build_centered_digit(
            ctx,
            digit,
            center_stud_x,
            center_stud_z,
            color,
        )
    )

    lines.append("0 -- Minifigures --")

    spacing = 8
    cols = 4
    rows = 3

    for row in range(rows):
        for col in range(cols):

            if row == 1 and col in (1, 2):
                continue

            x_offset = (col - (cols - 1) / 2) * spacing
            z_offset = (row - (rows - 1) / 2) * spacing

            fx = center_stud_x + x_offset
            fz = center_stud_z + z_offset

            lines.extend(
                build_minifig(
                    ctx,
                    template,
                    stud_x=fx,
                    stud_z=fz,
                )
            )

    lines.append("0 -- Frame --")

    lines.extend(build_group_frame(ctx, center_stud_x, center_stud_z))

    return lines


def build_groups_grid(ctx, template, cols, rows, color=15):

    studs_per_plate = 32
    lines = []

    add_section(lines, "ALL GROUPS")

    group_index = 1

    for r in range(rows):
        for c in range(cols):

            if group_index > 10:
                break

            row_offset = 1

            if group_index == 10:
                center_x = (cols // 2) * studs_per_plate
                center_z = (rows - 1 - r - row_offset) * studs_per_plate
            else:
                center_x = c * studs_per_plate
                center_z = (rows - 1 - r - row_offset) * studs_per_plate

            lines.extend(
                build_group(
                    ctx,
                    template,
                    str(group_index),
                    center_x,
                    center_z,
                    color,
                )
            )

            group_index += 1

        if group_index > 10:
            break

    return lines


def build_text_on_baseplate(
    ctx,
    text,
    plate_row,
    plate_col,
    grid_rows,
    studs_per_plate=32,
    color=15,
    margin=4,
    center=False,
    letter_spacing=1,
    delta_x=0,
    delta_z=0,
):
    """
    Render text inside a specific baseplate (grid row/col).

    Coordinate convention:
    - plate_col: 0 = left
    - plate_row: 0 = TOP row (top-left baseplate is (0,0))
    """

    # Convert "top-origin row index" to "bottom-origin row index"
    # so the computed Z matches the physical grid placement.
    row_from_bottom = (grid_rows - 1) - plate_row

    # Baseplate bottom-left corner in stud space
    base_x = plate_col * studs_per_plate
    base_z = row_from_bottom * studs_per_plate

    # Measure text width in studs
    total_width = 0
    for ch in text.upper():
        if ch not in LETTERS_5x7:
            raise ValueError(f"Unsupported character: {ch}")
        total_width += len(LETTERS_5x7[ch][0]) + letter_spacing
    total_width -= letter_spacing

    text_height = 7

    if center:
        start_x = base_x + (studs_per_plate - total_width) / 2
        start_z = base_z + (studs_per_plate - text_height) / 2
    else:
        start_x = base_x + margin
        start_z = base_z + margin

    start_x += delta_x
    start_z += delta_z

    return build_text_from_top_left(
        ctx,
        text,
        start_x,
        start_z,
        color=color,
        letter_spacing=letter_spacing,
    )


def main():
    project_dir = Path(__file__).parent
    build_dir = project_dir / "build"
    build_dir.mkdir(parents=True, exist_ok=True)

    # Scene reference plane (kept for backward compatibility).
    ctx = SceneContext(ground_y=0)

    cols = 3
    rows = 5

    # ---------------------------------------------------------------------
    # Build model
    # ---------------------------------------------------------------------

    lines = [
        "0 Plateau + digits test",
        "0 Name:  Untitled Model",
        "0 Author:  ",
        "0 CustomBrick",
        "0 FlexibleBrickControlPointUnitLength -1",
        "0 FlexibleBrickLockedControlPoint ",
        "0",
    ]

    # -------------------------
    # BASEPLATES
    # -------------------------
    add_section(lines, "BASEPLATES")

    lines.extend(build_baseplate_grid(ctx, cols=cols, rows=rows, color=1))

    # -------------------------
    # GROUPS (Digits + Minifigs + Frames)
    # -------------------------
    add_section(lines, "GROUPS")

    template_path = project_dir / "template" / "minifig.ldr"
    tpl = load_template(template_path)
    normalize_template_inplace(tpl)

    lines.extend(
        build_groups_grid(
            ctx,
            tpl,
            cols=cols,
            rows=rows,
            color=15,
        )
    )

    # -------------------------
    # TEXT
    # -------------------------
    add_section(lines, "TEXT - SOPHIE")

    lines.extend(
        build_text_on_baseplate(
            ctx,
            "SOPHIE",
            plate_row=0,
            plate_col=0,
            grid_rows=rows,
            center=True,
            delta_z=-4,
        )
    )

    add_section(lines, "TEXT - LAURENT")

    lines.extend(
        build_text_on_baseplate(
            ctx,
            "LAURENT",
            plate_row=0,
            plate_col=1,
            grid_rows=rows,
            center=True,
            delta_z=-18,
        )
    )
    # ---------------------------------------------------------------------
    # Export
    # ---------------------------------------------------------------------
    output_path = build_dir / "plateau_digits.ldr"
    output_path.write_text("\n".join(lines), encoding="utf-8")
    print(f"✅ File generated: {output_path}")

    bom = generate_bom_from_lines(lines)
    print_bom(bom)
    print_global_summary(bom)


if __name__ == "__main__":
    main()
