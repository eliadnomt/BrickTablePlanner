"""
brick.py

Indexes for standard LEGO bricks.
"""

from catalog import Categories, build_index_for_category

BRICKS = build_index_for_category(Categories.BRICKS)
