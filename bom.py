"""
bom.py

Bill of materials generation and reporting.

This module depends only on the central catalog.
It does not hardcode part categories locally.
"""

from collections import defaultdict

from catalog import Categories, Parts, get_category, get_size


def generate_bom_from_lines(lines):
    """
    Generate a BOM grouped by section markers.

    Sections are identified by lines of the form:
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

        part_id = line.split()[-1]
        bom[current_section][part_id] += 1

    return bom


def _clean_ref(part_id):
    return part_id.replace(".dat", "")


def _aggregate_parts(parts_dict):
    """
    Aggregate a dict {part_id: count} into:
    - category_totals for non-sized categories
    - detailed size buckets for sized categories
    """

    category_totals = defaultdict(int)
    size_details = defaultdict(lambda: defaultdict(int))
    total = 0

    for part_id, count in parts_dict.items():
        category = get_category(part_id)
        size = get_size(part_id)

        if size is None:
            category_totals[category] += count
        else:
            clean_ref = _clean_ref(part_id)
            size_details[category][(size, clean_ref)] += count

        total += count

    return category_totals, size_details, total


def _print_non_sized_categories(category_totals):
    """
    Print categories that do not carry a width/length size.
    """

    ordered_categories = [
        Categories.PLATE_32x32,
        Categories.PLATE_1x1,
        Categories.MINIFIG_HEAD,
        Categories.MINIFIG_TORSO,
        Categories.MINIFIG_ARMS,
        Categories.MINIFIG_HANDS,
        Categories.MINIFIG_LEGS,
        Categories.MINIFIG_ACCESSORY,
    ]

    subtotal = 0

    for category in ordered_categories:
        if category not in category_totals:
            continue

        if category == Categories.PLATE_32x32:
            ref = _clean_ref(Parts.PLATE_32x32)
            print(f"{category:20} ({ref})   x {category_totals[category]}")
        elif category == Categories.PLATE_1x1:
            ref = _clean_ref(Parts.PLATE_1x1)
            print(f"{category:20} ({ref})   x {category_totals[category]}")
        else:
            print(f"{category:20} x {category_totals[category]}")

        subtotal += category_totals[category]

    return subtotal


def _print_sized_category(title, details):
    """
    Print one sized category block (plates, bricks, tiles, etc).
    """

    subtotal = 0

    if not details:
        return subtotal

    print(f"{title}:")
    for (width, length), ref in sorted(details.keys()):
        count = details[((width, length), ref)]
        print(f"  {width}x{length:<3} ({ref})   x {count}")
        subtotal += count

    return subtotal


def print_bom(bom):
    """
    Print BOM grouped by section.
    """

    print("\n===== BILL OF MATERIALS =====\n")

    for section, parts in bom.items():
        print(f"--- {section} ---")

        category_totals, size_details, total = _aggregate_parts(parts)

        _print_non_sized_categories(category_totals)

        _print_sized_category(
            Categories.PLATES,
            size_details.get(Categories.PLATES, {}),
        )
        _print_sized_category(
            Categories.PLATES_MODIFIED,
            size_details.get(Categories.PLATES_MODIFIED, {}),
        )
        _print_sized_category(
            Categories.BRICKS,
            size_details.get(Categories.BRICKS, {}),
        )
        _print_sized_category(
            Categories.TILES,
            size_details.get(Categories.TILES, {}),
        )

        print(f"Total {section}: {total}\n")


def print_global_summary(bom):
    """
    Print a consolidated global summary across all sections.
    """

    global_counts = defaultdict(int)

    for section_parts in bom.values():
        for part_id, count in section_parts.items():
            global_counts[part_id] += count

    print("\n===== GLOBAL SUMMARY =====\n")

    category_totals, size_details, total = _aggregate_parts(global_counts)

    printed_total = 0
    printed_total += _print_non_sized_categories(category_totals)

    printed_total += _print_sized_category(
        Categories.PLATES,
        size_details.get(Categories.PLATES, {}),
    )
    printed_total += _print_sized_category(
        Categories.PLATES_MODIFIED,
        size_details.get(Categories.PLATES_MODIFIED, {}),
    )
    printed_total += _print_sized_category(
        Categories.BRICKS,
        size_details.get(Categories.BRICKS, {}),
    )
    printed_total += _print_sized_category(
        Categories.TILES,
        size_details.get(Categories.TILES, {}),
    )

    # printed_total should match total; keep total as source of truth
    print(f"\nTOTAL PIECES: {total}\n")


def format_bom_text(bom):
    """
    Return the BOM as a formatted string for display in the UI.
    """

    lines = []
    lines.append("===== BILL OF MATERIALS =====")
    lines.append("")

    for section, parts in bom.items():
        lines.append(f"--- {section} ---")

        category_totals, size_details, total = _aggregate_parts(parts)

        ordered_categories = [
            Categories.PLATE_32x32,
            Categories.PLATE_1x1,
            Categories.MINIFIG_HEAD,
            Categories.MINIFIG_TORSO,
            Categories.MINIFIG_ARMS,
            Categories.MINIFIG_HANDS,
            Categories.MINIFIG_LEGS,
            Categories.MINIFIG_ACCESSORY,
        ]

        for category in ordered_categories:
            if category not in category_totals:
                continue

            if category == Categories.PLATE_32x32:
                ref = _clean_ref(Parts.PLATE_32x32)
                lines.append(f"{category:20} ({ref})   x {category_totals[category]}")
            elif category == Categories.PLATE_1x1:
                ref = _clean_ref(Parts.PLATE_1x1)
                lines.append(f"{category:20} ({ref})   x {category_totals[category]}")
            else:
                lines.append(f"{category:20} x {category_totals[category]}")

        for category in [
            Categories.PLATES,
            Categories.PLATES_MODIFIED,
            Categories.BRICKS,
            Categories.TILES,
        ]:
            details = size_details.get(category, {})
            if not details:
                continue

            lines.append(f"{category}:")
            for (width, length), ref in sorted(details.keys()):
                count = details[((width, length), ref)]
                lines.append(f"  {width}x{length:<3} ({ref})   x {count}")

        lines.append(f"Total {section}: {total}")
        lines.append("")

    lines.append("===== GLOBAL SUMMARY =====")
    lines.append("")

    global_counts = defaultdict(int)
    for section_parts in bom.values():
        for part_id, count in section_parts.items():
            global_counts[part_id] += count

    category_totals, size_details, total = _aggregate_parts(global_counts)

    ordered_categories = [
        Categories.PLATE_32x32,
        Categories.PLATE_1x1,
        Categories.MINIFIG_HEAD,
        Categories.MINIFIG_TORSO,
        Categories.MINIFIG_ARMS,
        Categories.MINIFIG_HANDS,
        Categories.MINIFIG_LEGS,
        Categories.MINIFIG_ACCESSORY,
    ]

    for category in ordered_categories:
        if category not in category_totals:
            continue

        if category == Categories.PLATE_32x32:
            ref = _clean_ref(Parts.PLATE_32x32)
            lines.append(f"{category:20} ({ref})   x {category_totals[category]}")
        elif category == Categories.PLATE_1x1:
            ref = _clean_ref(Parts.PLATE_1x1)
            lines.append(f"{category:20} ({ref})   x {category_totals[category]}")
        else:
            lines.append(f"{category:20} x {category_totals[category]}")

    for category in [
        Categories.PLATES,
        Categories.PLATES_MODIFIED,
        Categories.BRICKS,
        Categories.TILES,
    ]:
        details = size_details.get(category, {})
        if not details:
            continue

        lines.append(f"{category}:")
        for (width, length), ref in sorted(details.keys()):
            count = details[((width, length), ref)]
            lines.append(f"  {width}x{length:<3} ({ref})   x {count}")

    lines.append("")
    lines.append(f"TOTAL PIECES: {total}")

    return "\n".join(lines)
