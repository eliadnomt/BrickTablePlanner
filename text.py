LETTERS_5x7 = {
    "A": [
        "..#..",
        ".#.#.",
        "#...#",
        "#####",
        "#...#",
        "#...#",
        "#...#",
    ],
    "B": [
        "####.",
        "#...#",
        "#...#",
        "####.",
        "#...#",
        "#...#",
        "####.",
    ],
    "C": [
        ".###.",
        "#...#",
        "#....",
        "#....",
        "#....",
        "#...#",
        ".###.",
    ],
    "D": [
        "####.",
        "#...#",
        "#...#",
        "#...#",
        "#...#",
        "#...#",
        "####.",
    ],
    "E": [
        "#####",
        "#....",
        "#....",
        "####.",
        "#....",
        "#....",
        "#####",
    ],
    "F": [
        "#####",
        "#....",
        "#....",
        "####.",
        "#....",
        "#....",
        "#....",
    ],
    "G": [
        ".###.",
        "#...#",
        "#....",
        "#.###",
        "#...#",
        "#...#",
        ".###.",
    ],
    "H": [
        "#...#",
        "#...#",
        "#...#",
        "#####",
        "#...#",
        "#...#",
        "#...#",
    ],
    "I": [
        "#####",
        "..#..",
        "..#..",
        "..#..",
        "..#..",
        "..#..",
        "#####",
    ],
    "J": [
        "..###",
        "...#.",
        "...#.",
        "...#.",
        "#..#.",
        "#..#.",
        ".##..",
    ],
    "K": [
        "#...#",
        "#..#.",
        "#.#..",
        "##...",
        "#.#..",
        "#..#.",
        "#...#",
    ],
    "L": [
        "#....",
        "#....",
        "#....",
        "#....",
        "#....",
        "#....",
        "#####",
    ],
    "M": [
        "#...#",
        "##.##",
        "#.#.#",
        "#.#.#",
        "#...#",
        "#...#",
        "#...#",
    ],
    "N": [
        "#...#",
        "##..#",
        "#.#.#",
        "#..##",
        "#...#",
        "#...#",
        "#...#",
    ],
    "O": [
        ".###.",
        "#...#",
        "#...#",
        "#...#",
        "#...#",
        "#...#",
        ".###.",
    ],
    "P": [
        "####.",
        "#...#",
        "#...#",
        "####.",
        "#....",
        "#....",
        "#....",
    ],
    "Q": [
        ".###.",
        "#...#",
        "#...#",
        "#...#",
        "#.#.#",
        "#..#.",
        ".##.#",
    ],
    "R": [
        "####.",
        "#...#",
        "#...#",
        "####.",
        "#.#..",
        "#..#.",
        "#...#",
    ],
    "S": [
        ".####",
        "#....",
        "#....",
        ".###.",
        "....#",
        "....#",
        "####.",
    ],
    "T": [
        "#####",
        "..#..",
        "..#..",
        "..#..",
        "..#..",
        "..#..",
        "..#..",
    ],
    "U": [
        "#...#",
        "#...#",
        "#...#",
        "#...#",
        "#...#",
        "#...#",
        ".###.",
    ],
    "V": [
        "#...#",
        "#...#",
        "#...#",
        "#...#",
        ".#.#.",
        ".#.#.",
        "..#..",
    ],
    "W": [
        "#...#",
        "#...#",
        "#...#",
        "#.#.#",
        "#.#.#",
        "##.##",
        "#...#",
    ],
    "X": [
        "#...#",
        "#...#",
        ".#.#.",
        "..#..",
        ".#.#.",
        "#...#",
        "#...#",
    ],
    "Y": [
        "#...#",
        "#...#",
        ".#.#.",
        "..#..",
        "..#..",
        "..#..",
        "..#..",
    ],
    "Z": [
        "#####",
        "....#",
        "...#.",
        "..#..",
        ".#...",
        "#....",
        "#####",
    ],
    "-": [
        ".....",
        ".....",
        "#####",
        ".....",
        ".....",
        ".....",
        ".....",
    ],
    " ": [
        ".....",
        ".....",
        ".....",
        ".....",
        ".....",
        ".....",
        ".....",
    ],
}


def measure_text(text, letter_spacing=1, line_spacing=1, vertical=False):
    if not text:
        return 0, 0

    char_width = 5
    char_height = 7

    if vertical:
        width = char_width
        height = len(text) * char_height + (len(text) - 1) * line_spacing
        return width, height

    width = len(text) * char_width + (len(text) - 1) * letter_spacing
    height = char_height
    return width, height


def build_text_from_top_left(
    ctx, text, start_stud_x, start_stud_z, color=15, letter_spacing=1
):
    """
    Render horizontal text from a top-left anchor.

    The anchor is snapped to the real stud grid used by this project:
    stud centers are on half-integer coordinates.
    """

    lines = []

    cursor_x = ctx.snap_to_stud(start_stud_x)
    start_stud_z = ctx.snap_to_stud(start_stud_z)

    for char in text.upper():
        if char not in LETTERS_5x7:
            raise ValueError(f"Unsupported character: {char}")

        bitmap = LETTERS_5x7[char]

        for row_index, row in enumerate(bitmap):
            for col_index, pixel in enumerate(row):
                if pixel != "#":
                    continue

                stud_x = cursor_x + col_index
                stud_z = start_stud_z - row_index

                x = ctx.studs(stud_x)
                z = ctx.studs(stud_z)
                y = ctx.baseplate_top_origin_y

                lines.append(
                    f"1 {color} {x:.6f} {y:.6f} {z:.6f} "
                    f"1 0 0 0 1 0 0 0 1 3024.dat"
                )

        cursor_x += 5 + letter_spacing

    return lines


def build_text_vertical_from_top_left(
    ctx, text, start_stud_x, start_stud_z, color=15, line_spacing=1
):
    """
    Render vertical text from a top-left anchor.

    The anchor is snapped to the real stud grid used by this project:
    stud centers are on half-integer coordinates.
    """

    lines = []

    start_stud_x = ctx.snap_to_stud(start_stud_x)
    cursor_z = ctx.snap_to_stud(start_stud_z)

    for char in text.upper():
        if char not in LETTERS_5x7:
            raise ValueError(f"Unsupported character: {char}")

        bitmap = LETTERS_5x7[char]

        for row_index, row in enumerate(bitmap):
            for col_index, pixel in enumerate(row):
                if pixel != "#":
                    continue

                stud_x = start_stud_x + col_index
                stud_z = cursor_z - row_index

                x = ctx.studs(stud_x)
                z = ctx.studs(stud_z)
                y = ctx.baseplate_top_origin_y

                lines.append(
                    f"1 {color} {x:.6f} {y:.6f} {z:.6f} "
                    f"1 0 0 0 1 0 0 0 1 3024.dat"
                )

        cursor_z -= 7 + line_spacing

    return lines
