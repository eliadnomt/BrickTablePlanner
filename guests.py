"""
Guest list parsing for the LEGO wedding seating chart generator.

A guest list is a spreadsheet (``.csv`` or ``.xlsx``) with a header row and
three columns:

================  ================================================================
Column            Meaning
================  ================================================================
first_name        The guest's first name. Required and unique (case-insensitive).
languages         Language(s) the guest speaks, separated by ``;`` or ``,``.
                  At least one language is required.
related_guests    First name(s) of guests this person should sit with, separated
                  by ``;`` or ``,``. May be left empty. Every name listed must
                  also appear in the ``first_name`` column.
================  ================================================================

Header names are matched case-insensitively and a handful of common aliases are
accepted (for example ``name`` for ``first_name`` or ``language(s) spoken`` for
``languages``).

Example ``guests.csv``::

    first_name,languages,related_guests
    Sophie,French,Laurent;Marie
    Laurent,French;English,Sophie
    Marie,French,Sophie
    Hans,German;English,
"""

from __future__ import annotations

import csv
from dataclasses import dataclass
from pathlib import Path


class GuestListError(ValueError):
    """Raised when a guest list file cannot be parsed into valid guests."""


@dataclass
class Guest:
    """A single guest parsed from a guest list."""

    name: str
    languages: list  # list[str] - original casing, order preserved, de-duplicated
    related: list  # list[str] - first names of related guests

    def speaks(self, language: str) -> bool:
        target = (language or "").strip().lower()
        return any(l.lower() == target for l in self.languages)

    def language_set(self):
        return {l.lower() for l in self.languages}


# --------------------------------------------------------------------------- #
# Header handling
# --------------------------------------------------------------------------- #

_NAME_ALIASES = {
    "first name",
    "firstname",
    "name",
    "guest",
    "guest name",
    "guest first name",
}
_LANGUAGE_ALIASES = {
    "languages",
    "language",
    "languages spoken",
    "language spoken",
    "langs",
    "spoken languages",
}
_RELATED_ALIASES = {
    "related guests",
    "related guest",
    "related",
    "relations",
    "relatives",
    "related to",
    "sits with",
}


def _normalise_header(value) -> str:
    text = str(value or "").strip().lower()
    text = text.replace("(", "").replace(")", "")
    text = text.replace("_", " ").replace("-", " ").replace("/", " ")
    return " ".join(text.split())


def _resolve_columns(header_row):
    indices = {"name": None, "languages": None, "related": None}
    for i, raw in enumerate(header_row):
        norm = _normalise_header(raw)
        if not norm:
            continue
        if indices["name"] is None and norm in _NAME_ALIASES:
            indices["name"] = i
        elif indices["languages"] is None and norm in _LANGUAGE_ALIASES:
            indices["languages"] = i
        elif indices["related"] is None and norm in _RELATED_ALIASES:
            indices["related"] = i

    missing = [key for key, value in indices.items() if value is None]
    if missing:
        pretty = {
            "name": "first_name",
            "languages": "languages",
            "related": "related_guests",
        }
        raise GuestListError(
            "Guest list is missing required column(s): "
            + ", ".join(pretty[m] for m in missing)
            + ". Expected a header row with columns: first_name, languages, related_guests."
        )
    return indices


# --------------------------------------------------------------------------- #
# Cell parsing
# --------------------------------------------------------------------------- #

def _cell(row, index) -> str:
    if index is None or index >= len(row):
        return ""
    value = row[index]
    if value is None:
        return ""
    return str(value).strip()


def split_multi_value(value) -> list:
    """Split a cell on ``;`` or ``,`` into a de-duplicated list of strings."""
    if value is None:
        return []
    text = str(value).strip()
    if not text:
        return []
    text = text.replace(",", ";")
    out = []
    seen = set()
    for part in text.split(";"):
        part = part.strip()
        if not part:
            continue
        key = part.lower()
        if key in seen:
            continue
        seen.add(key)
        out.append(part)
    return out


def _is_blank_row(row) -> bool:
    return all((cell is None or str(cell).strip() == "") for cell in row)


def _rows_to_guests(rows) -> list:
    cleaned = [list(r) for r in rows if not _is_blank_row(r)]
    if not cleaned:
        raise GuestListError("Guest list is empty (no header row found).")

    header = cleaned[0]
    columns = _resolve_columns(header)
    data_rows = cleaned[1:]
    if not data_rows:
        raise GuestListError("Guest list contains a header row but no guests.")

    guests = []
    seen_names = {}  # lower -> original
    for line_no, row in enumerate(data_rows, start=2):
        name = _cell(row, columns["name"])
        if not name:
            raise GuestListError(f"Row {line_no}: guest is missing a first name.")
        key = name.lower()
        if key in seen_names:
            raise GuestListError(
                f"Row {line_no}: duplicate guest name '{name}' "
                f"(already used by '{seen_names[key]}'). Guest names must be unique."
            )
        seen_names[key] = name

        languages = split_multi_value(_cell(row, columns["languages"]))
        if not languages:
            raise GuestListError(
                f"Row {line_no}: guest '{name}' has no language listed. "
                f"List at least one language, separated by ';' or ','."
            )

        related = split_multi_value(_cell(row, columns["related"]))
        guests.append(Guest(name=name, languages=languages, related=related))

    _validate_related_references(guests)
    return guests


def _validate_related_references(guests) -> None:
    known = {g.name.lower() for g in guests}
    for guest in guests:
        for related_name in guest.related:
            if related_name.lower() == guest.name.lower():
                raise GuestListError(
                    f"Guest '{guest.name}' lists themselves as a related guest."
                )
            if related_name.lower() not in known:
                raise GuestListError(
                    f"Guest '{guest.name}' lists related guest '{related_name}', "
                    f"who is not present in the guest list."
                )


# --------------------------------------------------------------------------- #
# File readers
# --------------------------------------------------------------------------- #

def _read_csv(path: Path) -> list:
    with open(path, "r", newline="", encoding="utf-8-sig") as handle:
        return [row for row in csv.reader(handle)]


def _read_xlsx(path: Path) -> list:
    try:
        import openpyxl
    except ImportError as exc:  # pragma: no cover - depends on environment
        raise GuestListError(
            "Reading .xlsx guest lists requires the 'openpyxl' package "
            "(pip install -r requirements.txt)."
        ) from exc

    try:
        workbook = openpyxl.load_workbook(path, read_only=True, data_only=True)
    except Exception as exc:  # openpyxl raises a variety of errors
        raise GuestListError(f"Could not read spreadsheet '{path}': {exc}") from exc

    try:
        sheet = workbook.active
        rows = []
        for raw in sheet.iter_rows(values_only=True):
            rows.append(list(raw))
        return rows
    finally:
        workbook.close()


def load_guest_list(path) -> list:
    """Load a guest list from a ``.csv`` or ``.xlsx`` file.

    Returns a list of :class:`Guest`. Raises :class:`GuestListError` with a
    human-readable message if the file is missing, the format is unsupported, or
    the contents are invalid.
    """
    path = Path(path)
    if not path.exists():
        raise GuestListError(f"Guest list file not found: {path}")

    suffix = path.suffix.lower()
    if suffix == ".csv":
        rows = _read_csv(path)
    elif suffix in (".xlsx", ".xlsm"):
        rows = _read_xlsx(path)
    else:
        raise GuestListError(
            f"Unsupported guest list format '{suffix or path.name}'. "
            f"Use a .csv or .xlsx file."
        )

    return _rows_to_guests(rows)
