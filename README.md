# LEGO Wedding Seating Chart Generator

A generic Python project that generates an LDraw wedding seating chart made of:

- LEGO baseplates
- numbered table groups
- LEGO minifigures around each table number
- configurable partner names
- configurable table topology
- configurable guest count by multiples of 10
- a small PySide6 UI

The generated `.ldr` file can be opened in BrickLink Studio.

## Features

- Partner names are configurable.
- Guest count is configurable by multiples of 10.
- The number of tables is automatically derived from the guest count.
- Table topology is configurable.
- Name placement depends on the chosen topology.
- A reusable minifig template is loaded from `template/minifig.ldr`.

## Project structure

- `main.py`: CLI entry point
- `ui.py`: PySide6 graphical interface
- `generator.py`: main generation logic
- `topologies.py`: table layout strategies
- `baseplate.py`: baseplate grid generation
- `digits.py`: 5x7 table number rendering
- `text.py`: 5x7 partner name rendering
- `minifig.py`: minifig template loader and placement
- `context.py`: geometric conversion helpers
- `template/minifig.ldr`: reusable minifig template

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

## UI usage

Run the PySide6 user interface:

```bash
python ui.py
```

In the UI you can change:

- Partner 1 name
- Partner 2 name
- Guest count (multiple of 10)
- Topology
- Output file
- Minifig template file

## Topologies

### `two_columns_center_names`

- Tables are arranged in two columns.
- Names are placed vertically in the center column.

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

## Notes

- The visual orientation of the minifigures is inherited from the existing project logic.
- The generated LDraw file is intended for BrickLink Studio.
- If PySide6 is not installed, `ui.py` will fail with an explicit message.

## Example output

The generated file is written by default to:

```text
build/wedding_seating_chart.ldr
```
