from context import BASEPLATE_THICKNESS


def build_minifig(ctx, template, stud_x, stud_z):
    """
    Place a normalized minifig template at the given stud position.

    Assumptions:
    - Template is already normalized in Y
    - stud_x / stud_z represent the desired center of the minifig in stud space
    - No rotation applied
    """

    # Recenter template in X/Z around its own geometric center
    cx = sum(p.x for p in template) / len(template)
    cz = sum(p.z for p in template) / len(template)

    dx = ctx.studs(stud_x)
    dz = ctx.studs(stud_z)
    dy = ctx.ground_y - BASEPLATE_THICKNESS

    out = []

    for p in template:
        final_x = (p.x - cx) + dx
        final_y = p.y + dy
        final_z = (p.z - cz) + dz

        out.append(
            f"1 {p.color} {final_x} {final_y} {final_z} "
            f"{p.a} {p.b} {p.c} {p.d} {p.e} {p.f} {p.g} {p.h} {p.i} "
            f"{p.part_id}"
        )

    return out
