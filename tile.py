"""
tile.py

Indexes for standard LEGO tiles.
"""

from catalog import Categories, build_index_for_category

TILES = build_index_for_category(Categories.TILES)
