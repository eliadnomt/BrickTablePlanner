from .part import Part
from .plates import PLATES
from .bricks import BRICKS
from .tiles import TILES
from .minifigs import MINIFIGS

Catalog = PLATES + BRICKS + TILES + MINIFIGS

__all__ = ["Part", "Catalog", "PLATES", "BRICKS", "TILES", "MINIFIGS"]
