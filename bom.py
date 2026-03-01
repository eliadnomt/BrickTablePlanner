from collections import defaultdict
from baseplate import PLATE_32x32
from brick import BRICKS, get_brick_size
from plate import get_plate_size, PLATES
from tile import get_tile_size, TILES

# ============================================================
# CLASSIFICATION
# ============================================================


def classify_part(part_id):
    """
    Strict classification of all parts used in this project.
    No fallback allowed.
    """

    part = part_id.replace(".dat", "")

    # ==================================================
    # BASEPLATE
    # ==================================================
    if part_id == PLATE_32x32:
        return "PLATE_32x32"

    # ==================================================
    # MINIFIG CORE PARTS
    # ==================================================
    if part.startswith("3626"):
        return "MINIFIG_HEAD"

    if part == "973":
        return "MINIFIG_TORSO"

    if part in {"3818", "3819"}:
        return "MINIFIG_ARMS"

    if part == "3820":
        return "MINIFIG_HANDS"

    if part in {"3815", "3816", "3817", "87609"}:
        return "MINIFIG_LEGS"

    # ==================================================
    # MINIFIG ACCESSORIES
    # ==================================================
    if part in {
        "88646",  # neck bracket
        "30414",  # armor
    }:
        return "MINIFIG_ACCESSORY"

    # ==================================================
    # BRICKS
    # ==================================================
    for width_dict in BRICKS.values():
        for ref in width_dict.values():
            if part == ref.replace(".dat", ""):
                return "BRICKS"

    # ==================================================
    # TILES
    # ==================================================
    for width_dict in TILES.values():
        for ref in width_dict.values():
            if part == ref.replace(".dat", ""):
                return "TILES"

    # ==================================================
    # STANDARD PLATES
    # ==================================================
    if part == "3024":
        return "PLATE_1x1"

    for width_dict in PLATES.values():
        for ref in width_dict.values():
            if part == ref.replace(".dat", ""):
                return "PLATES"

    # ==================================================
    # MODIFIED PLATES
    # ==================================================
    if part in {"2431"}:
        return "PLATES_MODIFIED"

    # ==================================================
    # STRICT MODE
    # ==================================================
    raise ValueError(f"Unknown part detected in BOM: {part_id}")


def generate_bom_from_lines(lines):
    """
    Generate BOM grouped by section markers.

    Sections are defined by:
        0 ===== SECTION NAME =====
    """

    bom = defaultdict(lambda: defaultdict(int))
    current_section = "UNDEFINED"

    for line in lines:

        line = line.strip()

        if line.startswith("0 ====="):
            current_section = line.replace("0 =====", "").replace("=====", "").strip()
            continue

        if not line.startswith("1 "):
            continue

        parts = line.split()
        part_id = parts[-1]

        bom[current_section][part_id] += 1

    return bom


# ============================================================
# PRINT BOM PER SECTION
# ============================================================


def print_bom(bom):
    """
    Print BOM grouped by section.
    Plates, bricks and tiles are detailed by size AND reference.
    """

    print("\n===== BILL OF MATERIALS =====\n")

    for section, parts in bom.items():

        print(f"--- {section} ---")

        category_totals = defaultdict(int)
        plate_details = defaultdict(int)
        brick_details = defaultdict(int)
        tile_details = defaultdict(int)

        total = 0

        for part_id, count in parts.items():

            category = classify_part(part_id)
            clean_ref = part_id.replace(".dat", "")

            if category == "PLATES":
                size = get_plate_size(part_id)
                if size:
                    plate_details[(size, clean_ref)] += count
                category_totals["PLATES"] += count

            elif category == "BRICKS":
                size = get_brick_size(part_id)
                if size:
                    brick_details[(size, clean_ref)] += count
                category_totals["BRICKS"] += count

            elif category == "TILES":
                size = get_tile_size(part_id)
                if size:
                    tile_details[(size, clean_ref)] += count
                category_totals["TILES"] += count

            else:
                category_totals[category] += count

            total += count

        # --- Print non size-based categories ---
        for category in sorted(category_totals.keys()):
            if category in {"PLATES", "BRICKS", "TILES"}:
                continue
            print(f"{category:20} x {category_totals[category]}")

        # --- Plates detail ---
        if plate_details:
            print("PLATES:")
            for (w, l), ref in sorted(plate_details.keys()):
                count = plate_details[((w, l), ref)]
                print(f"  {w}x{l:<3}  ({ref})   x {count}")

        # --- Bricks detail ---
        if brick_details:
            print("BRICKS:")
            for (w, l), ref in sorted(brick_details.keys()):
                count = brick_details[((w, l), ref)]
                print(f"  {w}x{l:<3}  ({ref})   x {count}")

        # --- Tiles detail ---
        if tile_details:
            print("TILES:")
            for (w, l), ref in sorted(tile_details.keys()):
                count = tile_details[((w, l), ref)]
                print(f"  {w}x{l:<3}  ({ref})   x {count}")

        print(f"Total {section}: {total}\n")


# ============================================================
# PRINT GLOBAL SUMMARY
# ============================================================


def print_global_summary(bom):
    """
    Print consolidated global summary.
    Plates, bricks and tiles are detailed by size AND reference.
    """

    global_counts = defaultdict(int)

    # Merge all sections
    for section_parts in bom.values():
        for part_id, count in section_parts.items():
            global_counts[part_id] += count

    print("\n===== GLOBAL SUMMARY =====\n")

    category_totals = defaultdict(int)
    plate_details = defaultdict(int)
    brick_details = defaultdict(int)
    tile_details = defaultdict(int)

    # ----------------------------------------------------
    # Aggregate
    # ----------------------------------------------------
    for part_id, count in global_counts.items():

        category = classify_part(part_id)
        clean_ref = part_id.replace(".dat", "")

        if category == "PLATES":
            size = get_plate_size(part_id)
            if size:
                plate_details[(size, clean_ref)] += count
            category_totals["PLATES"] += count

        elif category == "BRICKS":
            size = get_brick_size(part_id)
            if size:
                brick_details[(size, clean_ref)] += count
            category_totals["BRICKS"] += count

        elif category == "TILES":
            size = get_tile_size(part_id)
            if size:
                tile_details[(size, clean_ref)] += count
            category_totals["TILES"] += count

        else:
            category_totals[category] += count

    total_all = 0

    # ----------------------------------------------------
    # Print non size-based categories
    # ----------------------------------------------------
    for category in sorted(category_totals.keys()):

        if category in {"PLATES", "BRICKS", "TILES"}:
            continue

        if category == "PLATE_32x32":
            ref = PLATE_32x32.replace(".dat", "")
            print(f"{category:20} ({ref})   x {category_totals[category]}")
        else:
            print(f"{category:20} x {category_totals[category]}")

        total_all += category_totals[category]

    # ----------------------------------------------------
    # Plates
    # ----------------------------------------------------
    if plate_details:
        print("\nPLATES:")
        for (w, l), ref in sorted(plate_details.keys()):
            count = plate_details[((w, l), ref)]
            print(f"  {w}x{l:<3}  ({ref})   x {count}")
            total_all += count

    # ----------------------------------------------------
    # Bricks
    # ----------------------------------------------------
    if brick_details:
        print("\nBRICKS:")
        for (w, l), ref in sorted(brick_details.keys()):
            count = brick_details[((w, l), ref)]
            print(f"  {w}x{l:<3}  ({ref})   x {count}")
            total_all += count

    # ----------------------------------------------------
    # Tiles
    # ----------------------------------------------------
    if tile_details:
        print("\nTILES:")
        for (w, l), ref in sorted(tile_details.keys()):
            count = tile_details[((w, l), ref)]
            print(f"  {w}x{l:<3}  ({ref})   x {count}")
            total_all += count

    print(f"\nTOTAL PIECES: {total_all}\n")
