# LEGO Wedding Seating Chart Generator

A generic Python project that generates an LDraw wedding seating chart made of:

- LEGO baseplates
- numbered table groups
- LEGO minifigures around each table number
- configurable partner names
- configurable table topology
- configurable guest count by multiples of 10
- an optional spreadsheet guest list with an automatic seating optimiser
- a small PySide6 UI

The generated `.ldr` file can be opened in BrickLink Studio.

## Features

- Partner names are configurable.
- Guest count is configurable by multiples of 10.
- The number of tables is automatically derived from the guest count.
- Table topology is configurable.
- Name placement depends on the chosen topology.
- A reusable minifig template is loaded from `template/minifig.ldr`.
- A guest list (`.csv` or `.xlsx`) can be supplied. The seating optimiser keeps
  related guests together and keeps each table to a single shared language
  (bilingual guests can join either language group), and the UI shows the guest
  names colour-coded by language.

## Project structure

- `main.py`: CLI entry point
- `ui.py`: PySide6 graphical interface
- `generator.py`: main generation logic
- `topologies.py`: table layout strategies
- `guests.py`: guest list (`.csv` / `.xlsx`) parsing
- `seating.py`: seating optimiser and constraint validation
- `baseplate.py`: baseplate grid generation
- `digits.py`: 5x7 table number rendering
- `text.py`: 5x7 partner name rendering
- `minifig.py`: minifig template loader and placement
- `context.py`: geometric conversion helpers
- `topology_view.py`: PySide6 preview widget (topology schematic / seating chart)
- `template/minifig.ldr`: reusable minifig template
- `examples/guests_example.csv`: sample guest list

## Installation

Create a virtual environment if you want, then install dependencies:

```bash
pip install -r requirements.txt
```

## CLI usage

Generate the default project:

```bash
python main.py
```

Generate a custom project:

```bash
python main.py \
  --partner1 SOPHIE \
  --partner2 LAURENT \
  --guests 120 \
  --topology two_columns_center_names \
  --output build/custom_chart.ldr
```

Generate from a guest list (the optimiser decides the table count and
arrangement, so `--guests` is ignored):

```bash
python main.py \
  --partner1 SOPHIE \
  --partner2 LAURENT \
  --guest-list examples/guests_example.csv \
  --topology three_columns_bottom_names \
  --output build/custom_chart.ldr
```

If the guest list cannot be seated within the constraints (related guests
together, a shared language with both neighbours), the command prints the
specific offending placements and exits with a non-zero status without
generating a file.

## UI usage

Run the PySide6 user interface:

```bash
python ui.py
```

In the UI you can change:

- Spouse 1 name
- Spouse 2 name
- Guest count (multiple of 10) — disabled while a guest list is loaded
- Topology
- A guest list file (`.csv` / `.xlsx`) via **Load guest list…** / **Clear guest list**

The preview always shows the chosen topology — the table positions and partner-
name positions of the `.ldr` file. When a guest list is loaded, each table in
that layout is drawn with its seated guests arranged around the table (in seating
order, so neighbours are visible), colour-coded by spoken language; a legend of
language colours is shown on the left. If any guests cannot be seated within the
constraints, a dialog box lists exactly which placements violate them.

The on-screen guest-list format box and the `--guest-list` help also show a
small sample table.

## Topologies

### `two_columns_center_names`

- Tables are arranged in two columns, split as evenly as possible between them
  (numbered down the left column, then down the right column).
- Names are placed vertically in the center column.
- Supports up to 10 tables.

Example for 60 guests (6 tables):

```text
1   4
2   5
3   6
```

Example for 100 guests (10 tables):

```text
1   6
2   7
3   8
4   9
5  10
```

### `three_columns_bottom_names`

- Tables are arranged in three columns.
- Names are placed on the bottom row.

## Guest count logic

The guest count must be a positive multiple of 10.

Examples:

- 100 guests -> 10 tables
- 120 guests -> 12 tables
- 150 guests -> 15 tables

When a guest list is supplied instead, the number of tables comes from the
optimiser (each table seats 10), guests are distributed as evenly as possible
across the tables, and the guest count used for the LEGO model is rounded up to
the next multiple of 10 (extra seats are left empty).

## Guest list format

A guest list is a spreadsheet in **`.csv`** or **`.xlsx`** format with a header
row and exactly three columns:

| Column           | Required | Meaning                                                                                          |
| ---------------- | -------- | ------------------------------------------------------------------------------------------------ |
| `first_name`     | yes      | The guest's first name. Must be unique (case-insensitive).                                        |
| `languages`      | yes      | Language(s) the guest speaks, separated by `;` or `,`. At least one. Two or more = "bilingual".   |
| `related_guests` | yes      | First name(s) of guests this person should sit with, separated by `;` or `,`. May be left empty.  |

Notes:

- The header is matched case-insensitively, and common aliases are accepted
  (e.g. `name`, `language(s) spoken`, `related`).
- Every name in `related_guests` must also appear in the `first_name` column.
- A relationship only forces two guests onto the same table when it is
  **mutual** — both guests list each other. (A one-directional listing is still
  treated as a hint by the neighbour rule, but it does not group the two guests.)
  Mutual relationships are transitive: if A&B and B&C are both mutual, then A, B
  and C share a table.
- Empty rows are ignored.

Example (`examples/guests_example.csv`):

```csv
first_name,languages,related_guests
Sophie,French,Laurent;Marie
Laurent,French;English,Sophie
Marie,French,Sophie
Pierre,French,
Hans,German;English,Greta
Greta,German,Hans
Bob,English,Alice
Alice,English,Bob
```

## Seating optimiser

Given a guest list, the optimiser produces a seating chart that:

- keeps mutually-related guests at the same table;
- keeps each table to a single shared language so conversation flows — a
  bilingual guest may join any of their language groups;
- spreads guests evenly across the minimum number of tables for each language
  group (no near-empty straggler tables);
- guarantees the **neighbour rule**: every guest has, on each side, a neighbour
  who is either related to them or shares a language with them.

A table is round and seats 10. A full table is treated as a closed circle (the
first and last guests are neighbours); a partly filled table is treated as a
line because the empty seats break the circle.

If the constraints cannot all be satisfied — for example a related group with
more than 10 members, more tables than the chosen layout supports, or a "star"
of mutually related guests who share no language with each other — the optimiser
reports the specific offending placements. The CLI prints them to stderr and
exits non-zero; the UI shows them in a dialog box.

## Notes

- The visual orientation of the minifigures is inherited from the existing project logic.
- The generated LDraw file is intended for BrickLink Studio.
- If PySide6 is not installed, `ui.py` will fail with an explicit message.

## Example output

The generated file is written by default to:

```text
build/wedding_seating_chart.ldr
```
