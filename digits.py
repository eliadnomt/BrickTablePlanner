from catalog import Parts

DIGITS_5x7 = {
    "1": [
        "..#..",
        ".##..",
        "..#..",
        "..#..",
        "..#..",
        "..#..",
        ".###.",
    ],
    "2": [
        ".###.",
        "#...#",
        "....#",
        "..##.",
        ".#...",
        "#....",
        "#####",
    ],
    "3": [
        "####.",
        "....#",
        "..##.",
        "....#",
        "....#",
        "#...#",
        ".###.",
    ],
    "4": [
        "#..#.",
        "#..#.",
        "#..#.",
        "#####",
        "...#.",
        "...#.",
        "...#.",
    ],
    "5": [
        "#####",
        "#....",
        "####.",
        "....#",
        "....#",
        "#...#",
        ".###.",
    ],
    "6": [
        ".###.",
        "#....",
        "####.",
        "#...#",
        "#...#",
        "#...#",
        ".###.",
    ],
    "7": [
        "#####",
        "....#",
        "...#.",
        "..#..",
        ".#...",
        "#....",
        "#....",
    ],
    "8": [
        ".###.",
        "#...#",
        "#...#",
        ".###.",
        "#...#",
        "#...#",
        ".###.",
    ],
    "9": [
        ".###.",
        "#...#",
        "#...#",
        ".####",
        "....#",
        "...#.",
        ".##..",
    ],
    "0": [
        ".###.",
        "#...#",
        "#..##",
        "#.#.#",
        "##..#",
        "#...#",
        ".###.",
    ],
}


def render_text_5x7(text, gap=1):
    if not text:
        raise ValueError("Empty text")

    rows = [""] * 7
    for index, char in enumerate(text):
        if char not in DIGITS_5x7:
            raise ValueError(f"Unsupported digit: {char}")
        glyph = DIGITS_5x7[char]
        for row_index in range(7):
            rows[row_index] += glyph[row_index]
        if index < len(text) - 1:
            for row_index in range(7):
                rows[row_index] += "." * gap

    return rows


def measure_digit_text(text, gap=1):
    matrix = render_text_5x7(text, gap=gap)
    return len(matrix[0]), len(matrix)


def build_centered_digit(ctx, text, center_stud_x, center_stud_z, color=15):
    matrix = render_text_5x7(text)
    height = len(matrix)
    width = len(matrix[0])

    origin_x = center_stud_x - (width - 1) / 2
    origin_z = center_stud_z - (height - 1) / 2

    lines = []

    # ---------------------------------------------------------------------
    # Stud grid alignment correction
    #
    # Baseplates are positioned by their geometric center.
    # However, LEGO studs are positioned on integer coordinates.
    #
    # A half-stud offset ensures the bitmap aligns exactly on the stud grid.
    # ---------------------------------------------------------------------
    half_stud = 0.5

    for row_index, row in enumerate(matrix):
        for col_index, pixel in enumerate(row):
            if pixel != "#":
                continue

            stud_x = origin_x + col_index
            stud_z = origin_z + (height - 1 - row_index)

            x = ctx.studs(stud_x)
            z = ctx.studs(stud_z)
            y = ctx.baseplate_top_origin_y - half_stud

            lines.append(
                f"1 {color} {x:.6f} {y:.6f} {z:.6f} 1 0 0 0 1 0 0 0 1 {Parts.PLATE_1x1}"
            )

    return lines
