"""
catalog.py

Central part catalog for the project.

This module is the single source of truth for:
- logical categories
- known part references
- size metadata when relevant

All other modules should depend on this catalog.
"""


class Categories:
    PLATE_32x32 = "PLATE_32x32"
    PLATE_1x1 = "PLATE_1x1"
    PLATES = "PLATES"
    PLATES_MODIFIED = "PLATES_MODIFIED"
    BRICKS = "BRICKS"
    TILES = "TILES"
    MINIFIG_HEAD = "MINIFIG_HEAD"
    MINIFIG_TORSO = "MINIFIG_TORSO"
    MINIFIG_ARMS = "MINIFIG_ARMS"
    MINIFIG_HANDS = "MINIFIG_HANDS"
    MINIFIG_LEGS = "MINIFIG_LEGS"
    MINIFIG_ACCESSORY = "MINIFIG_ACCESSORY"


class Parts:
    # --------------------------------------------------
    # Baseplates
    # --------------------------------------------------
    PLATE_32x32 = "3811.dat"

    # --------------------------------------------------
    # Plates
    # --------------------------------------------------
    PLATE_1x1 = "3024.dat"

    PLATE_1x2 = "3023.dat"
    PLATE_1x3 = "3623.dat"
    PLATE_1x4 = "3710.dat"
    PLATE_1x6 = "3666.dat"
    PLATE_1x8 = "3460.dat"
    PLATE_1x10 = "4477.dat"
    PLATE_1x12 = "60479.dat"

    PLATE_2x2 = "3022.dat"
    PLATE_2x3 = "3021.dat"
    PLATE_2x4 = "3020.dat"
    PLATE_2x6 = "3795.dat"
    PLATE_2x8 = "3034.dat"
    PLATE_2x10 = "3832.dat"
    PLATE_2x12 = "2445.dat"

    # --------------------------------------------------
    # Modified plates
    # --------------------------------------------------
    PLATE_MOD_1x4 = "2431.dat"
    PLATE_MOD_1x2 = "3023b.dat"

    # --------------------------------------------------
    # Bricks
    # --------------------------------------------------
    BRICK_1x1 = "3005.dat"
    BRICK_1x2 = "3004.dat"
    BRICK_1x3 = "3622.dat"
    BRICK_1x4 = "3010.dat"
    BRICK_1x6 = "3009.dat"
    BRICK_1x8 = "3008.dat"

    BRICK_2x2 = "3003.dat"
    BRICK_2x3 = "3002.dat"
    BRICK_2x4 = "3001.dat"
    BRICK_2x6 = "2456.dat"
    BRICK_2x8 = "3007.dat"

    # --------------------------------------------------
    # Tiles
    # --------------------------------------------------
    TILE_1x1 = "3070b.dat"
    TILE_1x2 = "3069b.dat"
    TILE_1x3 = "63864.dat"
    TILE_1x4 = "2431b.dat"
    TILE_1x6 = "6636.dat"
    TILE_1x8 = "4162.dat"

    TILE_2x2 = "3068b.dat"
    TILE_2x3 = "26603.dat"
    TILE_2x4 = "87079.dat"
    TILE_2x6 = "69729.dat"

    # --------------------------------------------------
    # Minifig parts
    # --------------------------------------------------
    MINIFIG_HEAD = "3626.dat"
    MINIFIG_HEAD_PRINTED = "3626cp01.dat"

    MINIFIG_TORSO = "973.dat"

    MINIFIG_ARM_LEFT = "3818.dat"
    MINIFIG_ARM_RIGHT = "3819.dat"

    MINIFIG_HAND = "3820.dat"

    MINIFIG_LEG_LEFT = "3816.dat"
    MINIFIG_LEG_RIGHT = "3817.dat"
    MINIFIG_HIPS = "3815.dat"
    MINIFIG_LEGS_ASSEMBLY = "87609.dat"

    MINIFIG_NECK_BRACKET = "88646.dat"
    MINIFIG_ARMOR = "30414.dat"
    MINIFIG_PANEL = "2420.dat"


PARTS = {
    # --------------------------------------------------
    # Baseplates
    # --------------------------------------------------
    Parts.PLATE_32x32: {
        "category": Categories.PLATE_32x32,
        "label": "32x32",
    },
    # --------------------------------------------------
    # Plates
    # --------------------------------------------------
    Parts.PLATE_1x1: {
        "category": Categories.PLATE_1x1,
        "width": 1,
        "length": 1,
    },
    Parts.PLATE_1x2: {
        "category": Categories.PLATES,
        "width": 1,
        "length": 2,
    },
    Parts.PLATE_1x3: {
        "category": Categories.PLATES,
        "width": 1,
        "length": 3,
    },
    Parts.PLATE_1x4: {
        "category": Categories.PLATES,
        "width": 1,
        "length": 4,
    },
    Parts.PLATE_1x6: {
        "category": Categories.PLATES,
        "width": 1,
        "length": 6,
    },
    Parts.PLATE_1x8: {
        "category": Categories.PLATES,
        "width": 1,
        "length": 8,
    },
    Parts.PLATE_1x10: {
        "category": Categories.PLATES,
        "width": 1,
        "length": 10,
    },
    Parts.PLATE_1x12: {
        "category": Categories.PLATES,
        "width": 1,
        "length": 12,
    },
    Parts.PLATE_2x2: {
        "category": Categories.PLATES,
        "width": 2,
        "length": 2,
    },
    Parts.PLATE_2x3: {
        "category": Categories.PLATES,
        "width": 2,
        "length": 3,
    },
    Parts.PLATE_2x4: {
        "category": Categories.PLATES,
        "width": 2,
        "length": 4,
    },
    Parts.PLATE_2x6: {
        "category": Categories.PLATES,
        "width": 2,
        "length": 6,
    },
    Parts.PLATE_2x8: {
        "category": Categories.PLATES,
        "width": 2,
        "length": 8,
    },
    Parts.PLATE_2x10: {
        "category": Categories.PLATES,
        "width": 2,
        "length": 10,
    },
    Parts.PLATE_2x12: {
        "category": Categories.PLATES,
        "width": 2,
        "length": 12,
    },
    # --------------------------------------------------
    # Modified plates
    # --------------------------------------------------
    Parts.PLATE_MOD_1x4: {
        "category": Categories.PLATES_MODIFIED,
        "width": 1,
        "length": 4,
    },
    Parts.PLATE_MOD_1x2: {
        "category": Categories.PLATES_MODIFIED,
        "width": 1,
        "length": 2,
    },
    # --------------------------------------------------
    # Bricks
    # --------------------------------------------------
    Parts.BRICK_1x1: {
        "category": Categories.BRICKS,
        "width": 1,
        "length": 1,
    },
    Parts.BRICK_1x2: {
        "category": Categories.BRICKS,
        "width": 1,
        "length": 2,
    },
    Parts.BRICK_1x3: {
        "category": Categories.BRICKS,
        "width": 1,
        "length": 3,
    },
    Parts.BRICK_1x4: {
        "category": Categories.BRICKS,
        "width": 1,
        "length": 4,
    },
    Parts.BRICK_1x6: {
        "category": Categories.BRICKS,
        "width": 1,
        "length": 6,
    },
    Parts.BRICK_1x8: {
        "category": Categories.BRICKS,
        "width": 1,
        "length": 8,
    },
    Parts.BRICK_2x2: {
        "category": Categories.BRICKS,
        "width": 2,
        "length": 2,
    },
    Parts.BRICK_2x3: {
        "category": Categories.BRICKS,
        "width": 2,
        "length": 3,
    },
    Parts.BRICK_2x4: {
        "category": Categories.BRICKS,
        "width": 2,
        "length": 4,
    },
    Parts.BRICK_2x6: {
        "category": Categories.BRICKS,
        "width": 2,
        "length": 6,
    },
    Parts.BRICK_2x8: {
        "category": Categories.BRICKS,
        "width": 2,
        "length": 8,
    },
    # --------------------------------------------------
    # Tiles
    # --------------------------------------------------
    Parts.TILE_1x1: {
        "category": Categories.TILES,
        "width": 1,
        "length": 1,
    },
    Parts.TILE_1x2: {
        "category": Categories.TILES,
        "width": 1,
        "length": 2,
    },
    Parts.TILE_1x3: {
        "category": Categories.TILES,
        "width": 1,
        "length": 3,
    },
    Parts.TILE_1x4: {
        "category": Categories.TILES,
        "width": 1,
        "length": 4,
    },
    Parts.TILE_1x6: {
        "category": Categories.TILES,
        "width": 1,
        "length": 6,
    },
    Parts.TILE_1x8: {
        "category": Categories.TILES,
        "width": 1,
        "length": 8,
    },
    Parts.TILE_2x2: {
        "category": Categories.TILES,
        "width": 2,
        "length": 2,
    },
    Parts.TILE_2x3: {
        "category": Categories.TILES,
        "width": 2,
        "length": 3,
    },
    Parts.TILE_2x4: {
        "category": Categories.TILES,
        "width": 2,
        "length": 4,
    },
    Parts.TILE_2x6: {
        "category": Categories.TILES,
        "width": 2,
        "length": 6,
    },
    # --------------------------------------------------
    # Minifig
    # --------------------------------------------------
    Parts.MINIFIG_HEAD: {
        "category": Categories.MINIFIG_HEAD,
    },
    Parts.MINIFIG_HEAD_PRINTED: {
        "category": Categories.MINIFIG_HEAD,
    },
    Parts.MINIFIG_TORSO: {
        "category": Categories.MINIFIG_TORSO,
    },
    Parts.MINIFIG_ARM_LEFT: {
        "category": Categories.MINIFIG_ARMS,
    },
    Parts.MINIFIG_ARM_RIGHT: {
        "category": Categories.MINIFIG_ARMS,
    },
    Parts.MINIFIG_HAND: {
        "category": Categories.MINIFIG_HANDS,
    },
    Parts.MINIFIG_HIPS: {
        "category": Categories.MINIFIG_LEGS,
    },
    Parts.MINIFIG_LEG_LEFT: {
        "category": Categories.MINIFIG_LEGS,
    },
    Parts.MINIFIG_LEG_RIGHT: {
        "category": Categories.MINIFIG_LEGS,
    },
    Parts.MINIFIG_LEGS_ASSEMBLY: {
        "category": Categories.MINIFIG_LEGS,
    },
    Parts.MINIFIG_NECK_BRACKET: {
        "category": Categories.MINIFIG_ACCESSORY,
    },
    Parts.MINIFIG_ARMOR: {
        "category": Categories.MINIFIG_ACCESSORY,
    },
    Parts.MINIFIG_PANEL: {
        "category": Categories.MINIFIG_ACCESSORY,
    },
}


def get_category(part_id):
    if part_id not in PARTS:
        raise ValueError(f"Unknown part detected in catalog lookup: {part_id}")
    return PARTS[part_id]["category"]


def get_metadata(part_id):
    if part_id not in PARTS:
        raise ValueError(f"Unknown part detected in catalog metadata lookup: {part_id}")
    return PARTS[part_id]


def get_size(part_id):
    metadata = get_metadata(part_id)
    width = metadata.get("width")
    length = metadata.get("length")
    if width is None or length is None:
        return None
    return width, length


def build_index_for_category(category):
    """
    Build a {width: {length: part_id}} index for one category.
    Useful for plates, bricks, tiles, etc.
    """

    index = {}

    for part_id, metadata in PARTS.items():
        if metadata["category"] != category:
            continue

        width = metadata.get("width")
        length = metadata.get("length")

        if width is None or length is None:
            continue

        index.setdefault(width, {})[length] = part_id

    return index
