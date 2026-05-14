from dataclasses import dataclass
from typing import Optional


@dataclass
class Part:
    label: str
    file_name: str
    category: str
    modified: bool
    width: Optional[int] = None
    length: Optional[int] = None
