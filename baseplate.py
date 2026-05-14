def build_baseplate_grid(ctx, cols, rows, color=1, origin_x_stud=0, origin_z_stud=0):
    lines = []

    for r in range(rows):
        for c in range(cols):
            x = ctx.studs(origin_x_stud + c * 32)
            y = ctx.baseplate_origin_y
            z = ctx.studs(origin_z_stud + r * 32)
            lines.append(
                f"1 {color} {x:.6f} {y:.6f} {z:.6f} 1 0 0 0 1 0 0 0 1 3811.dat"
            )

    return lines
