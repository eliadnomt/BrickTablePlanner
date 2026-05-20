"""
Tests for the guest-list-driven seating chart feature:

* guest list parsing (CSV and XLSX, separators, validation errors)
* related-guest components
* the seating optimiser (keeps related guests together, single-language tables,
  bilingual guests flexible, reports violations when infeasible)
* the neighbour-rule validator
* integration with the LDraw model generator

The path to the project root is added to sys.path by test/conftest.py, so the
top-level modules import cleanly here just like in test_catalog.py.
"""

import csv
import os

import pytest

from guests import Guest, GuestListError, load_guest_list, split_multi_value
from seating import (
    SEATS_PER_TABLE,
    SeatingResult,
    common_languages,
    optimize_seating,
    related_components,
    validate_seating,
)
from generator import generate_model


HEADER = ["first_name", "languages", "related_guests"]


# --------------------------------------------------------------------------- #
# Helpers
# --------------------------------------------------------------------------- #

def _write_csv(tmp_path, rows, name="guests.csv"):
    path = tmp_path / name
    with open(path, "w", newline="", encoding="utf-8") as handle:
        csv.writer(handle).writerows(rows)
    return str(path)


def _write_xlsx(tmp_path, rows, name="guests.xlsx"):
    openpyxl = pytest.importorskip("openpyxl")
    workbook = openpyxl.Workbook()
    sheet = workbook.active
    for row in rows:
        sheet.append(list(row))
    path = tmp_path / name
    workbook.save(path)
    return str(path)


def _g(name, languages, related=None):
    return Guest(name=name, languages=list(languages), related=list(related or []))


def _by_name(tables):
    return [[g.name for g in table] for table in tables]


def _same_table(tables, a, b):
    for table in tables:
        names = {g.name for g in table}
        if a in names and b in names:
            return True
    return False


# --------------------------------------------------------------------------- #
# Guest list parsing
# --------------------------------------------------------------------------- #

class TestGuestListParsing:
    def test_load_csv_basic(self, tmp_path):
        path = _write_csv(tmp_path, [
            HEADER,
            ["Sophie", "French", "Laurent;Marie"],
            ["Laurent", "French;English", "Sophie"],
            ["Marie", "French", "Sophie"],
        ])
        guests = load_guest_list(path)
        assert [g.name for g in guests] == ["Sophie", "Laurent", "Marie"]
        assert guests[1].languages == ["French", "English"]
        assert guests[0].related == ["Laurent", "Marie"]

    def test_load_xlsx_basic(self, tmp_path):
        path = _write_xlsx(tmp_path, [
            HEADER,
            ["Anna", "German", "Bob"],
            ["Bob", "German;English", "Anna"],
        ])
        guests = load_guest_list(path)
        assert [g.name for g in guests] == ["Anna", "Bob"]
        assert guests[1].languages == ["German", "English"]

    def test_header_aliases_and_case_insensitive(self, tmp_path):
        path = _write_csv(tmp_path, [
            ["Name", "Language(s) Spoken", "Related Guests"],
            ["Yves", "French", ""],
        ])
        guests = load_guest_list(path)
        assert guests[0].name == "Yves"
        assert guests[0].languages == ["French"]
        assert guests[0].related == []

    def test_language_and_related_separators(self):
        assert split_multi_value("French; English , Spanish") == ["French", "English", "Spanish"]
        assert split_multi_value("Sophie,Marie;Sophie") == ["Sophie", "Marie"]
        assert split_multi_value("") == []
        assert split_multi_value(None) == []

    def test_blank_rows_skipped(self, tmp_path):
        path = _write_csv(tmp_path, [
            HEADER,
            ["", "", ""],
            ["Carl", "English", ""],
            ["", "", ""],
        ])
        guests = load_guest_list(path)
        assert [g.name for g in guests] == ["Carl"]

    def test_missing_column_raises(self, tmp_path):
        path = _write_csv(tmp_path, [
            ["first_name", "languages"],
            ["X", "French"],
        ])
        with pytest.raises(GuestListError):
            load_guest_list(path)

    def test_missing_name_raises(self, tmp_path):
        path = _write_csv(tmp_path, [HEADER, ["", "French", ""]])
        with pytest.raises(GuestListError):
            load_guest_list(path)

    def test_missing_language_raises(self, tmp_path):
        path = _write_csv(tmp_path, [HEADER, ["Sam", "", ""]])
        with pytest.raises(GuestListError):
            load_guest_list(path)

    def test_duplicate_name_raises(self, tmp_path):
        path = _write_csv(tmp_path, [
            HEADER,
            ["Sam", "French", ""],
            ["sam", "English", ""],
        ])
        with pytest.raises(GuestListError):
            load_guest_list(path)

    def test_unknown_related_reference_raises(self, tmp_path):
        path = _write_csv(tmp_path, [HEADER, ["Sam", "French", "Nobody"]])
        with pytest.raises(GuestListError):
            load_guest_list(path)

    def test_self_reference_raises(self, tmp_path):
        path = _write_csv(tmp_path, [HEADER, ["Sam", "French", "Sam"]])
        with pytest.raises(GuestListError):
            load_guest_list(path)

    def test_unsupported_extension_raises(self, tmp_path):
        path = tmp_path / "guests.txt"
        path.write_text("first_name,languages,related_guests\nA,French,\n")
        with pytest.raises(GuestListError):
            load_guest_list(str(path))

    def test_missing_file_raises(self, tmp_path):
        with pytest.raises(GuestListError):
            load_guest_list(str(tmp_path / "does_not_exist.csv"))

    def test_empty_file_raises(self, tmp_path):
        path = _write_csv(tmp_path, [])
        with pytest.raises(GuestListError):
            load_guest_list(path)

    def test_header_only_raises(self, tmp_path):
        path = _write_csv(tmp_path, [HEADER])
        with pytest.raises(GuestListError):
            load_guest_list(path)


# --------------------------------------------------------------------------- #
# Related-guest components
# --------------------------------------------------------------------------- #

class TestRelatedComponents:
    def test_isolated_guests_are_singletons(self):
        guests = [_g("A", ["X"]), _g("B", ["X"]), _g("C", ["X"])]
        comps = related_components(guests)
        assert sorted(len(c) for c in comps) == [1, 1, 1]

    def test_mutual_relationships_are_transitive(self):
        guests = [
            _g("A", ["X"], ["B"]),
            _g("B", ["X"], ["A", "C"]),
            _g("C", ["X"], ["B"]),
            _g("D", ["X"]),
        ]
        comps = related_components(guests)
        sizes = sorted(len(c) for c in comps)
        assert sizes == [1, 3]
        big = next(c for c in comps if len(c) == 3)
        assert {g.name for g in big} == {"A", "B", "C"}

    def test_relationship_requires_mutual_listing(self):
        # B lists A, but A does not list B -> they are NOT grouped.
        guests = [_g("A", ["X"]), _g("B", ["X"], ["A"])]
        comps = related_components(guests)
        assert len(comps) == 2

    def test_one_directional_chain_does_not_blob(self):
        # A->B->C->D->E->F, each listing only the next; none mutual.
        names = ["A", "B", "C", "D", "E", "F"]
        guests = [
            _g(name, ["X"], [names[i + 1]] if i + 1 < len(names) else [])
            for i, name in enumerate(names)
        ]
        comps = related_components(guests)
        assert len(comps) == 6
        assert all(len(c) == 1 for c in comps)

    def test_common_languages(self):
        assert common_languages([_g("A", ["French", "English"]), _g("B", ["English"])]) == ["English"]
        assert common_languages([_g("A", ["French"]), _g("B", ["German"])]) == []


# --------------------------------------------------------------------------- #
# Optimiser - feasible cases
# --------------------------------------------------------------------------- #

class TestOptimizerFeasible:
    def test_empty_guest_list(self):
        result = optimize_seating([])
        assert isinstance(result, SeatingResult)
        assert result.feasible
        assert result.tables == []

    def test_related_guests_seated_together(self):
        guests = [
            _g("Sophie", ["French"], ["Laurent", "Marie"]),
            _g("Laurent", ["French", "English"], ["Sophie"]),
            _g("Marie", ["French"], ["Sophie"]),
            _g("Bob", ["English"]),
            _g("Alice", ["English"]),
            _g("Hans", ["German"]),
        ]
        result = optimize_seating(guests)
        assert result.feasible
        assert _same_table(result.tables, "Sophie", "Laurent")
        assert _same_table(result.tables, "Sophie", "Marie")
        # No guest is dropped or duplicated.
        seated = [g.name for table in result.tables for g in table]
        assert sorted(seated) == sorted(g.name for g in guests)

    def test_single_language_tables(self):
        guests = (
            [_g(f"F{i}", ["French"]) for i in range(8)]
            + [_g(f"E{i}", ["English"]) for i in range(6)]
            + [_g(f"D{i}", ["German"]) for i in range(3)]
        )
        result = optimize_seating(guests)
        assert result.feasible
        # Every table of unrelated guests shares a common language.
        for table in result.tables:
            assert common_languages(table), _by_name([table])

    def test_bilingual_guest_is_flexible(self):
        # Five French speakers (a full-ish French table would be 5), plus a
        # bilingual French/English speaker who must join the French group, plus
        # English speakers. Everything should fit feasibly.
        guests = (
            [_g(f"F{i}", ["French"]) for i in range(9)]
            + [_g("Bridge", ["French", "English"])]
            + [_g(f"E{i}", ["English"]) for i in range(6)]
        )
        result = optimize_seating(guests)
        assert result.feasible
        # The bilingual guest joins a table where everyone shares one of her
        # languages.
        for table in result.tables:
            names = {g.name for g in table}
            if "Bridge" in names:
                assert common_languages(table)

    def test_mixed_language_related_pair_is_allowed(self):
        # A and B speak different languages but are related -> they sit together
        # and the neighbour rule is still satisfied (they are related).
        guests = [_g("A", ["French"], ["B"]), _g("B", ["German"], ["A"])]
        result = optimize_seating(guests)
        assert result.feasible
        assert _same_table(result.tables, "A", "B")

    def test_validates_clean_after_optimisation(self):
        guests = [
            _g("A", ["French"], ["B"]),
            _g("B", ["French", "English"], ["A"]),  # mutual with A
            _g("C", ["English"], ["D"]),
            _g("D", ["English"], ["C"]),            # mutual with C
            _g("E", ["German"]),
        ]
        result = optimize_seating(guests)
        assert result.feasible
        assert validate_seating(result.tables) == []

    def test_distributes_evenly_within_a_language(self):
        # 23 guests, all the same language, none related -> 3 tables, balanced.
        guests = [_g(f"G{i:02d}", ["French"]) for i in range(23)]
        result = optimize_seating(guests)
        assert result.feasible
        sizes = sorted(len(t) for t in result.tables)
        assert sum(sizes) == 23
        assert len(sizes) == 3            # ceil(23 / 10)
        assert max(sizes) - min(sizes) <= 1   # evenly spread
        assert min(sizes) >= 2            # no near-empty straggler table

    def test_keeps_minimum_table_count(self):
        guests = [_g(f"G{i:02d}", ["French"]) for i in range(20)]
        result = optimize_seating(guests)
        assert result.feasible
        assert result.table_count == 2
        assert sorted(len(t) for t in result.tables) == [10, 10]

    def _seat_adjacent(self, table, a, b):
        names = [g.name for g in table]
        i, j = names.index(a), names.index(b)
        return abs(i - j) == 1 or {i, j} == {0, len(names) - 1}

    def test_couples_not_split_when_separate_components(self):
        # Two couples (each a mutual pair) plus some singletons, all one
        # language. Each couple must stay side by side.
        guests = [
            _g("Nicole", ["French"], ["Fabrice"]),
            _g("Fabrice", ["French"], ["Nicole"]),
            _g("William", ["French"], ["Myriam"]),
            _g("Myriam", ["French"], ["William"]),
            _g("Bob", ["French"]),
            _g("Alice", ["French"]),
        ]
        result = optimize_seating(guests)
        assert result.feasible
        table = next(t for t in result.tables if any(g.name == "Nicole" for g in t))
        assert self._seat_adjacent(table, "Nicole", "Fabrice")
        assert self._seat_adjacent(table, "William", "Myriam")

    def test_couples_not_split_within_a_larger_related_group(self):
        # Two couples linked by a mutual friendship (one transitive group of 4),
        # all the same language. The couples must still sit together.
        guests = [
            _g("Nicole", ["French"], ["Fabrice"]),
            _g("Fabrice", ["French"], ["Nicole", "William"]),
            _g("William", ["French"], ["Fabrice", "Myriam"]),
            _g("Myriam", ["French"], ["William"]),
        ]
        result = optimize_seating(guests)
        assert result.feasible
        table = result.tables[0]
        assert {g.name for g in table} == {"Nicole", "Fabrice", "William", "Myriam"}
        assert self._seat_adjacent(table, "Nicole", "Fabrice")
        assert self._seat_adjacent(table, "William", "Myriam")


# --------------------------------------------------------------------------- #
# Optimiser - infeasible cases
# --------------------------------------------------------------------------- #

class TestOptimizerInfeasible:
    def test_related_group_larger_than_table(self):
        size = SEATS_PER_TABLE + 2
        guests = [
            _g(f"P{i}", ["X"], [f"P{j}" for j in range(size) if j != i])
            for i in range(size)
        ]
        result = optimize_seating(guests)
        assert not result.feasible
        assert any("seats only" in v for v in result.violations)
        # All guests are still present in the (best-effort) arrangement.
        seated = [g.name for table in result.tables for g in table]
        assert sorted(seated) == sorted(g.name for g in guests)

    def test_too_many_tables_for_layout(self):
        guests = [_g(f"G{i}", ["French"]) for i in range(25)]
        result = optimize_seating(guests, max_tables=1)
        assert not result.feasible
        assert any("only supports 1" in v or "1 table" in v for v in result.violations)

    def test_star_with_incompatible_leaves_reports_pair(self):
        guests = [
            _g("Center", ["Spanish"], ["Anna", "Bob", "Dan"]),
            _g("Anna", ["French"], ["Center"]),
            _g("Bob", ["German"], ["Center"]),
            _g("Dan", ["Italian"], ["Center"]),
        ]
        result = optimize_seating(guests)
        assert not result.feasible
        # The violation must name the two guests that cannot sit next to each
        # other.
        joined = " ".join(result.violations)
        assert "Bob" in joined and "Dan" in joined


# --------------------------------------------------------------------------- #
# Neighbour-rule validator
# --------------------------------------------------------------------------- #

class TestValidateSeating:
    def test_ok_when_all_share_language(self):
        table = [_g("A", ["French"]), _g("B", ["French"]), _g("C", ["French"])]
        assert validate_seating([table]) == []

    def test_ok_when_related_chain(self):
        table = [_g("A", ["French"], ["B"]), _g("B", ["German"], ["A", "C"]), _g("C", ["Italian"], ["B"])]
        assert validate_seating([table]) == []

    def test_flags_incompatible_neighbours(self):
        table = [_g("A", ["French"]), _g("B", ["German"]), _g("C", ["French"])]
        violations = validate_seating([table])
        assert violations
        assert any("A" in v and "B" in v for v in violations)

    def test_full_table_is_a_circle(self):
        # First and last guests are neighbours when the table is full.
        table = (
            [_g("Odd", ["Klingon"])]
            + [_g(f"F{i}", ["French"]) for i in range(SEATS_PER_TABLE - 1)]
        )
        assert len(table) == SEATS_PER_TABLE
        violations = validate_seating([table])
        # "Odd" is wedged between two French speakers it shares nothing with.
        assert len(violations) >= 2

    def test_partly_filled_table_is_a_line(self):
        table = [_g("Odd", ["Klingon"])] + [_g(f"F{i}", ["French"]) for i in range(3)]
        # Only one bad seam (Odd next to F0); the other end is an empty seat.
        violations = validate_seating([table])
        assert len(violations) == 1

    def test_single_guest_table_is_valid(self):
        assert validate_seating([[_g("Solo", ["French"])]]) == []


# --------------------------------------------------------------------------- #
# Integration with the LDraw generator
# --------------------------------------------------------------------------- #

class TestIntegrationWithGenerator:
    def test_generate_model_with_guest_derived_count(self, tmp_path):
        guests = (
            [_g(f"F{i}", ["French"]) for i in range(8)]
            + [_g(f"E{i}", ["English"]) for i in range(6)]
        )
        result = optimize_seating(guests)
        assert result.feasible
        table_count = max(result.table_count, 1)

        out = tmp_path / "chart.ldr"
        gen = generate_model(
            partner1="SOPHIE",
            partner2="LAURENT",
            guest_count=table_count * 10,
            topology_key="three_columns_bottom_names",
            output_path=str(out),
        )
        assert os.path.isfile(out)
        assert gen["table_count"] == table_count
        # The LDraw file itself is unchanged by the guest feature: no names in it.
        assert out.read_text().startswith("0 LEGO Wedding Seating Chart")
