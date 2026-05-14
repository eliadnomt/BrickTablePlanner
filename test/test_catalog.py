"""
Test suite for the refactored catalog.

Tests cover:
- Dataclass structure (Part)
- Catalog list contents and completeness
- Category assignments and consolidation
- Label formatting
- Modified flag logic
- Width/length parameters
- Getter functions (get_category, get_metadata, get_size)
- build_index_for_category
- Directory / module structure
"""

import importlib
import os
import dataclasses
import pytest


ROOT = os.path.join(os.path.dirname(__file__), "..")
CATALOG_DIR = os.path.join(ROOT, "catalog")


# ---------------------------------------------------------------------------
# 1. Directory and module structure
# ---------------------------------------------------------------------------

class TestCatalogDirectoryStructure:
    def test_catalog_directory_exists(self):
        assert os.path.isdir(CATALOG_DIR), "A 'catalog' directory should exist in the project root"

    def test_old_catalog_mono_file_removed(self):
        assert not os.path.isfile(
            os.path.join(ROOT, "catalog.py")
        ), "The old monolithic catalog.py should be removed from the project root"

    def test_catalog_is_package(self):
        init_path = os.path.join(CATALOG_DIR, "__init__.py")
        assert os.path.isfile(init_path), "catalog/ should be a Python package (has __init__.py)"

    def test_one_file_per_category(self):
        py_files = [
            f for f in os.listdir(CATALOG_DIR)
            if f.endswith(".py") and f != "__init__.py"
        ]
        category_files = [f for f in py_files if f not in ("getters.py", "build_index.py")]
        assert len(category_files) >= 4, (
            "There should be at least one file per category (PLATES, BRICKS, TILES, MINIFIGS)"
        )

    def test_getters_in_separate_file(self):
        assert os.path.isfile(
            os.path.join(CATALOG_DIR, "getters.py")
        ), "Getter functions should be in catalog/getters.py"

    def test_build_index_in_separate_file(self):
        assert os.path.isfile(
            os.path.join(CATALOG_DIR, "build_index.py")
        ), "build_index_for_category should be in catalog/build_index.py"


# ---------------------------------------------------------------------------
# 2. Part dataclass
# ---------------------------------------------------------------------------

def _import_catalog():
    import catalog
    return catalog


def _get_catalog_list():
    cat = _import_catalog()
    candidates = ["Catalog", "catalog", "CATALOG"]
    for name in candidates:
        obj = getattr(cat, name, None)
        if obj is not None and isinstance(obj, list):
            return obj
    pytest.fail("Could not find a Catalog list exported from the catalog package")


def _get_part_class():
    cat = _import_catalog()
    part_cls = getattr(cat, "Part", None)
    if part_cls is None:
        pytest.fail("Could not find a Part class exported from the catalog package")
    return part_cls


class TestPartDataclass:
    def test_part_is_dataclass(self):
        Part = _get_part_class()
        assert dataclasses.is_dataclass(Part), "Part must be a dataclass"

    def test_required_fields_present(self):
        Part = _get_part_class()
        field_names = {f.name for f in dataclasses.fields(Part)}
        for required in ("label", "file_name", "category", "modified"):
            assert required in field_names, f"Part dataclass must have a '{required}' field"

    def test_optional_fields_include_width_length(self):
        Part = _get_part_class()
        field_names = {f.name for f in dataclasses.fields(Part)}
        assert "width" in field_names, "Part dataclass should have an optional 'width' field"
        assert "length" in field_names, "Part dataclass should have an optional 'length' field"

    def test_modified_is_boolean(self):
        Part = _get_part_class()
        fields = {f.name: f for f in dataclasses.fields(Part)}
        mod_field = fields["modified"]
        assert mod_field.type is bool or mod_field.type == "bool", (
            "The 'modified' field should be typed as bool"
        )

    def test_dot_indexing_access(self):
        Part = _get_part_class()
        p = Part(label="1x2", file_name="3023.dat", category="PLATES", modified=False, width=1, length=2)
        assert p.label == "1x2"
        assert p.file_name == "3023.dat"
        assert p.category == "PLATES"
        assert p.modified is False
        assert p.width == 1
        assert p.length == 2

    def test_no_part_id_field(self):
        Part = _get_part_class()
        field_names = {f.name for f in dataclasses.fields(Part)}
        assert "part_id" not in field_names, (
            "References to 'part_id' should be standardised to 'file_name'"
        )


# ---------------------------------------------------------------------------
# 3. Catalog list (replaces Parts dict)
# ---------------------------------------------------------------------------

class TestCatalogList:
    def test_catalog_is_list(self):
        catalog_list = _get_catalog_list()
        assert isinstance(catalog_list, list)

    def test_catalog_not_empty(self):
        catalog_list = _get_catalog_list()
        assert len(catalog_list) > 0

    def test_all_entries_are_part_instances(self):
        Part = _get_part_class()
        catalog_list = _get_catalog_list()
        for entry in catalog_list:
            assert isinstance(entry, Part), f"Every entry in Catalog should be a Part, got {type(entry)}"

    def test_total_part_count(self):
        catalog_list = _get_catalog_list()
        assert len(catalog_list) == 52, (
            "The catalog should contain all 52 original parts"
        )

    def test_file_names_are_unique(self):
        catalog_list = _get_catalog_list()
        file_names = [p.file_name for p in catalog_list]
        assert len(file_names) == len(set(file_names)), "Each part should have a unique file_name"


# ---------------------------------------------------------------------------
# 4. Categories
# ---------------------------------------------------------------------------

VALID_CATEGORIES = {"PLATES", "BRICKS", "TILES", "MINIFIGS"}


class TestCategories:
    def test_only_valid_categories(self):
        catalog_list = _get_catalog_list()
        categories = {p.category for p in catalog_list}
        assert categories <= VALID_CATEGORIES, (
            f"Only these categories are allowed: {VALID_CATEGORIES}. Found: {categories}"
        )

    def test_all_categories_present(self):
        catalog_list = _get_catalog_list()
        categories = {p.category for p in catalog_list}
        assert categories == VALID_CATEGORIES

    def test_plates_modified_merged(self):
        catalog_list = _get_catalog_list()
        categories = {p.category for p in catalog_list}
        assert "PLATES_MODIFIED" not in categories, "PLATES_MODIFIED should be merged into PLATES"

    def test_minifig_subcategories_merged(self):
        catalog_list = _get_catalog_list()
        categories = {p.category for p in catalog_list}
        for old_cat in ("MINIFIG_HEAD", "MINIFIG_TORSO", "MINIFIG_ARMS",
                        "MINIFIG_HANDS", "MINIFIG_LEGS", "MINIFIG_ACCESSORY"):
            assert old_cat not in categories, f"{old_cat} should be merged into MINIFIGS"


# ---------------------------------------------------------------------------
# 5. Modified flag
# ---------------------------------------------------------------------------

class TestModifiedFlag:
    def test_modified_plates_flagged(self):
        catalog_list = _get_catalog_list()
        mod_plate_ids = {"2431.dat", "3023b.dat"}
        for p in catalog_list:
            if p.file_name in mod_plate_ids:
                assert p.modified is True, (
                    f"Part {p.file_name} was in PLATES_MODIFIED and should have modified=True"
                )

    def test_regular_plates_not_modified(self):
        catalog_list = _get_catalog_list()
        unmodified_plate_ids = {"3023.dat", "3623.dat", "3710.dat", "3666.dat"}
        for p in catalog_list:
            if p.file_name in unmodified_plate_ids:
                assert p.modified is False, (
                    f"Part {p.file_name} was in PLATES (not MODIFIED) and should have modified=False"
                )

    def test_plate_32x32_not_modified(self):
        catalog_list = _get_catalog_list()
        for p in catalog_list:
            if p.file_name == "3811.dat":
                assert p.modified is False, "PLATE_32x32 should be treated as unmodified"
                assert p.category == "PLATES"

    def test_plate_1x1_not_modified(self):
        catalog_list = _get_catalog_list()
        for p in catalog_list:
            if p.file_name == "3024.dat":
                assert p.modified is False, "PLATE_1x1 should be treated as unmodified"
                assert p.category == "PLATES"

    def test_bricks_not_modified(self):
        catalog_list = _get_catalog_list()
        for p in catalog_list:
            if p.category == "BRICKS":
                assert p.modified is False

    def test_tiles_not_modified(self):
        catalog_list = _get_catalog_list()
        for p in catalog_list:
            if p.category == "TILES":
                assert p.modified is False

    def test_minifigs_not_modified(self):
        catalog_list = _get_catalog_list()
        for p in catalog_list:
            if p.category == "MINIFIGS":
                assert p.modified is False


# ---------------------------------------------------------------------------
# 6. Labels
# ---------------------------------------------------------------------------

class TestLabels:
    def test_plate_labels_width_x_length(self):
        catalog_list = _get_catalog_list()
        for p in catalog_list:
            if p.category == "PLATES" and p.width is not None and p.length is not None:
                assert p.label == f"{p.width}x{p.length}", (
                    f"PLATES label for {p.file_name} should be '{p.width}x{p.length}', got '{p.label}'"
                )

    def test_brick_labels_width_x_length(self):
        catalog_list = _get_catalog_list()
        for p in catalog_list:
            if p.category == "BRICKS":
                assert p.label == f"{p.width}x{p.length}", (
                    f"BRICKS label for {p.file_name} should be '{p.width}x{p.length}', got '{p.label}'"
                )

    def test_tile_labels_width_x_length(self):
        catalog_list = _get_catalog_list()
        for p in catalog_list:
            if p.category == "TILES":
                assert p.label == f"{p.width}x{p.length}", (
                    f"TILES label for {p.file_name} should be '{p.width}x{p.length}', got '{p.label}'"
                )

    def test_minifig_head_label(self):
        catalog_list = _get_catalog_list()
        for p in catalog_list:
            if p.file_name == "3626.dat":
                assert p.label == "head", f"MINIFIG_HEAD label should be 'head', got '{p.label}'"

    def test_minifig_torso_label(self):
        catalog_list = _get_catalog_list()
        for p in catalog_list:
            if p.file_name == "973.dat":
                assert p.label == "torso", f"MINIFIG_TORSO label should be 'torso', got '{p.label}'"

    def test_minifig_arm_left_label(self):
        catalog_list = _get_catalog_list()
        for p in catalog_list:
            if p.file_name == "3818.dat":
                assert p.label == "arm left", (
                    f"MINIFIG_ARM_LEFT label should be 'arm left', got '{p.label}'"
                )

    def test_minifig_arm_right_label(self):
        catalog_list = _get_catalog_list()
        for p in catalog_list:
            if p.file_name == "3819.dat":
                assert p.label == "arm right", (
                    f"MINIFIG_ARM_RIGHT label should be 'arm right', got '{p.label}'"
                )

    def test_minifig_hand_label(self):
        catalog_list = _get_catalog_list()
        for p in catalog_list:
            if p.file_name == "3820.dat":
                assert p.label == "hand", f"MINIFIG_HAND label should be 'hand', got '{p.label}'"

    def test_minifig_leg_left_label(self):
        catalog_list = _get_catalog_list()
        for p in catalog_list:
            if p.file_name == "3816.dat":
                assert p.label == "leg left", (
                    f"MINIFIG_LEG_LEFT label should be 'leg left', got '{p.label}'"
                )

    def test_minifig_hips_label(self):
        catalog_list = _get_catalog_list()
        for p in catalog_list:
            if p.file_name == "3815.dat":
                assert p.label == "hips", f"MINIFIG_HIPS label should be 'hips', got '{p.label}'"

    def test_minifig_legs_assembly_label(self):
        catalog_list = _get_catalog_list()
        for p in catalog_list:
            if p.file_name == "87609.dat":
                assert p.label == "legs assembly", (
                    f"MINIFIG_LEGS_ASSEMBLY label should be 'legs assembly', got '{p.label}'"
                )

    def test_minifig_neck_bracket_label(self):
        catalog_list = _get_catalog_list()
        for p in catalog_list:
            if p.file_name == "88646.dat":
                assert p.label == "neck bracket", (
                    f"MINIFIG_NECK_BRACKET label should be 'neck bracket', got '{p.label}'"
                )

    def test_minifig_head_printed_label(self):
        catalog_list = _get_catalog_list()
        for p in catalog_list:
            if p.file_name == "3626cp01.dat":
                assert p.label == "head printed", (
                    f"MINIFIG_HEAD_PRINTED label should be 'head printed', got '{p.label}'"
                )

    def test_plate_32x32_label(self):
        catalog_list = _get_catalog_list()
        for p in catalog_list:
            if p.file_name == "3811.dat":
                assert p.label == "32x32"

    def test_plate_1x1_label(self):
        catalog_list = _get_catalog_list()
        for p in catalog_list:
            if p.file_name == "3024.dat":
                assert p.label == "1x1"


# ---------------------------------------------------------------------------
# 7. Width and length
# ---------------------------------------------------------------------------

class TestWidthLength:
    def test_plates_have_width_and_length(self):
        catalog_list = _get_catalog_list()
        for p in catalog_list:
            if p.category == "PLATES":
                assert p.width is not None and p.length is not None, (
                    f"PLATES part {p.file_name} should have width and length"
                )

    def test_bricks_have_width_and_length(self):
        catalog_list = _get_catalog_list()
        for p in catalog_list:
            if p.category == "BRICKS":
                assert p.width is not None and p.length is not None, (
                    f"BRICKS part {p.file_name} should have width and length"
                )

    def test_tiles_have_width_and_length(self):
        catalog_list = _get_catalog_list()
        for p in catalog_list:
            if p.category == "TILES":
                assert p.width is not None and p.length is not None, (
                    f"TILES part {p.file_name} should have width and length"
                )

    def test_minifigs_no_width_length(self):
        catalog_list = _get_catalog_list()
        for p in catalog_list:
            if p.category == "MINIFIGS":
                assert p.width is None and p.length is None, (
                    f"MINIFIGS part {p.file_name} should not have width/length"
                )

    def test_plate_32x32_dimensions(self):
        catalog_list = _get_catalog_list()
        for p in catalog_list:
            if p.file_name == "3811.dat":
                assert p.width == 32 and p.length == 32

    def test_plate_1x1_dimensions(self):
        catalog_list = _get_catalog_list()
        for p in catalog_list:
            if p.file_name == "3024.dat":
                assert p.width == 1 and p.length == 1

    def test_specific_brick_dimensions(self):
        catalog_list = _get_catalog_list()
        expected = {
            "3005.dat": (1, 1),
            "3004.dat": (1, 2),
            "3001.dat": (2, 4),
            "3007.dat": (2, 8),
        }
        found = {}
        for p in catalog_list:
            if p.file_name in expected:
                found[p.file_name] = (p.width, p.length)
        for fn, dims in expected.items():
            assert found.get(fn) == dims, f"Brick {fn} should be {dims}, got {found.get(fn)}"

    def test_specific_tile_dimensions(self):
        catalog_list = _get_catalog_list()
        expected = {
            "3070b.dat": (1, 1),
            "3069b.dat": (1, 2),
            "87079.dat": (2, 4),
            "69729.dat": (2, 6),
        }
        found = {}
        for p in catalog_list:
            if p.file_name in expected:
                found[p.file_name] = (p.width, p.length)
        for fn, dims in expected.items():
            assert found.get(fn) == dims, f"Tile {fn} should be {dims}, got {found.get(fn)}"


# ---------------------------------------------------------------------------
# 8. Specific part entries (spot checks)
# ---------------------------------------------------------------------------

class TestSpecificParts:
    def test_modified_plate_1x4(self):
        catalog_list = _get_catalog_list()
        part = next((p for p in catalog_list if p.file_name == "2431.dat"), None)
        assert part is not None, "Modified plate 1x4 (2431.dat) must be in catalog"
        assert part.category == "PLATES"
        assert part.modified is True
        assert part.width == 1
        assert part.length == 4
        assert part.label == "1x4"

    def test_modified_plate_1x2(self):
        catalog_list = _get_catalog_list()
        part = next((p for p in catalog_list if p.file_name == "3023b.dat"), None)
        assert part is not None, "Modified plate 1x2 (3023b.dat) must be in catalog"
        assert part.category == "PLATES"
        assert part.modified is True
        assert part.width == 1
        assert part.length == 2

    def test_minifig_armor(self):
        catalog_list = _get_catalog_list()
        part = next((p for p in catalog_list if p.file_name == "30414.dat"), None)
        assert part is not None, "MINIFIG_ARMOR (30414.dat) must be in catalog"
        assert part.category == "MINIFIGS"
        assert part.label == "armor"

    def test_minifig_panel(self):
        catalog_list = _get_catalog_list()
        part = next((p for p in catalog_list if p.file_name == "2420.dat"), None)
        assert part is not None, "MINIFIG_PANEL (2420.dat) must be in catalog"
        assert part.category == "MINIFIGS"
        assert part.label == "panel"


# ---------------------------------------------------------------------------
# 9. Getter functions
# ---------------------------------------------------------------------------
from catalog.utils import get_category, get_size, get_metadata
class TestGetCategory:
    def test_get_category_plates(self):
        assert get_category("3023.dat") == "PLATES"

    def test_get_category_bricks(self):
        
        assert get_category("3005.dat") == "BRICKS"

    def test_get_category_tiles(self):
        
        assert get_category("3070b.dat") == "TILES"

    def test_get_category_minifigs(self):
        
        assert get_category("3626.dat") == "MINIFIGS"

    def test_get_category_modified_plate_returns_plates(self):
        
        assert get_category("2431.dat") == "PLATES"

    def test_get_category_unknown_raises(self):
        
        with pytest.raises(ValueError):
            get_category("unknown.dat")

    def test_get_category_uses_file_name(self):
        
        assert get_category("3811.dat") == "PLATES"


class TestGetMetadata:
    def test_get_metadata_returns_part(self):
        
        Part = _get_part_class()
        result = get_metadata("3023.dat")
        assert isinstance(result, Part)

    def test_get_metadata_correct_fields(self):
        
        result = get_metadata("3023.dat")
        assert result.file_name == "3023.dat"
        assert result.category == "PLATES"
        assert result.width == 1
        assert result.length == 2

    def test_get_metadata_unknown_raises(self):
        
        with pytest.raises(ValueError):
            get_metadata("fake_part.dat")


class TestGetSize:
    def test_get_size_plate(self):
        
        result = get_size("3023.dat")
        assert result == (1, 2)

    def test_get_size_brick(self):
        
        result = get_size("3001.dat")
        assert result == (2, 4)

    def test_get_size_tile(self):
        
        result = get_size("87079.dat")
        assert result == (2, 4)

    def test_get_size_minifig_returns_none(self):
        
        result = get_size("3626.dat")
        assert result is None

    def test_get_size_plate_32x32(self):
        
        result = get_size("3811.dat")
        assert result == (32, 32)


# ---------------------------------------------------------------------------
# 10. build_index_for_category
# ---------------------------------------------------------------------------
from catalog.utils import build_index_for_category
class TestBuildIndex:
    def test_build_index_returns_dict(self):

        index = build_index_for_category("PLATES")
        assert isinstance(index, dict)

    def test_build_index_plates_structure(self):

        index = build_index_for_category("PLATES")
        assert 1 in index
        assert 2 in index[1]
        assert index[1][2] == "3023.dat"

    def test_build_index_bricks(self):
        
        index = build_index_for_category("BRICKS")
        assert index[1][1] == "3005.dat"
        assert index[2][4] == "3001.dat"

    def test_build_index_tiles(self):
        
        index = build_index_for_category("TILES")
        assert index[1][1] == "3070b.dat"

    def test_build_index_minifigs_empty(self):
        
        index = build_index_for_category("MINIFIGS")
        assert index == {}

    def test_build_index_unknown_category_empty(self):
        
        index = build_index_for_category("NONEXISTENT")
        assert index == {}

    def test_build_index_includes_modified_plates(self):
        
        index = build_index_for_category("PLATES")
        assert index.get(1, {}).get(4) is not None, (
            "Modified plate 1x4 should be included when building index for PLATES"
        )

    def test_build_index_includes_32x32(self):
        
        index = build_index_for_category("PLATES")
        assert 32 in index and 32 in index[32], (
            "32x32 baseplate should be included in PLATES index"
        )


# ---------------------------------------------------------------------------
# 11. Importability from catalog package
# ---------------------------------------------------------------------------

class TestImports:
    def test_import_catalog_package(self):
        import catalog
        assert hasattr(catalog, "Part") or hasattr(catalog, "part")

    def test_import_get_category(self):
        
        assert callable(get_category)

    def test_import_get_metadata(self):
        
        assert callable(get_metadata)

    def test_import_get_size(self):
        
        assert callable(get_size)

    def test_import_build_index_for_category(self):
        
        assert callable(build_index_for_category)

    def test_catalog_list_importable(self):
        _get_catalog_list()
