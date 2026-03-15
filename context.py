from dataclasses import dataclass

STUD = 20
BASEPLATE_THICKNESS = 8


@dataclass
class SceneContext:
    ground_y: float = 0.0

    def studs(self, value):
        return value * STUD

    def snap_to_stud(self, value):
        """
        Snap a stud-space coordinate to the nearest real stud center.

        In this project, baseplates are positioned by their geometric center
        on integer stud coordinates. Actual stud centers therefore lie on
        half-integer coordinates (..., -0.5, 0.5, 1.5, ...).
        """
        return round(value - 0.5) + 0.5

    @property
    def baseplate_origin_y(self):
        return self.ground_y + BASEPLATE_THICKNESS / 2

    @property
    def baseplate_top_origin_y(self):
        return self.ground_y - BASEPLATE_THICKNESS / 2
