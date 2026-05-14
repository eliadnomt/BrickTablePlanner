"""
plate.py

Helpers and indexes for standard LEGO plates.
"""

from catalog.utils import build_index_for_category, get_metadata

PLATE_1x1 = "3024.dat"
PLATES = build_index_for_category("PLATES")


def build_plate(ctx, stud_x, stud_z, color, length):
    """
    Place a 1xN plate aligned on the X axis.
    """

    if length not in PLATES[1]:
        raise ValueError(f"No 1x{length} plate found in catalog")

    x = ctx.studs(stud_x)
    z = ctx.studs(stud_z)
    y = ctx.baseplate_top_origin_y
    part = PLATES[1][length]

    return f"1 {color} {x:.6f} {y:.6f} {z:.6f} 1 0 0 0 1 0 0 0 1 {part}"


def build_plate_rotated(ctx, stud_x, stud_z, color, length):
    """
    Place a 1xN plate rotated 90 degrees around Y,
    so its length runs along the Z axis.
    """

    if length not in PLATES[1]:
        raise ValueError(f"No 1x{length} plate found in catalog")

    x = ctx.studs(stud_x)
    z = ctx.studs(stud_z)
    y = ctx.baseplate_top_origin_y
    part = PLATES[1][length]

    return f"1 {color} {x:.6f} {y:.6f} {z:.6f} 0 0 1 0 1 0 -1 0 0 {part}"
