from dataclasses import dataclass

STUD = 20
BASEPLATE_THICKNESS = 8


@dataclass
class SceneContext:
    ground_y: float = 0.0

    def studs(self, value):
        return value * STUD

    @property
    def baseplate_origin_y(self):
        return self.ground_y + BASEPLATE_THICKNESS / 2

    @property
    def baseplate_top_origin_y(self):
        return self.ground_y - BASEPLATE_THICKNESS / 2
