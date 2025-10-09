from vpython import canvas, box, color, vector, sphere, distant_light, rate
import numpy as np
from types import SimpleNamespace


def coordinates():
    """
    Returns the x-z coordinates of various tennis court regions.
    """
    court = SimpleNamespace()
    court.x = 23.77 / 2  # total length
    court.z = 10.97 / 2  # total width doubles

    single_court = SimpleNamespace()
    single_court.x = 23.77 / 2
    single_court.z = 8.23 / 2

    serve_box = SimpleNamespace()
    serve_box.x = 6.40  # distance from net to service line
    serve_box.z = 8.23 / 2  # half-width of singles service box
    # deep = SimpleNamespace()
    # wide = SimpleNamespace()
    # vole = SimpleNamespace()
    # centre = SimpleNamespace()
    return court, single_court, serve_box


class TennisCourt:
    def __init__(self):
        # Dimensions in meters (scaled to include surroundings)
        self.image = SimpleNamespace()
        self.image.x = 25.9781
        self.image.z = 16.5201

        self.court_xz, self.single_court, self.serve_box = coordinates()

        self.stand_z = 6.15

        self.scene = None
        self.court_type = None
        self.test = np.array([0, 0, 0])

        # Available court textures
        self.court_textures = {
            "hard": "assets/tennis_court_background.jpg",
            "clay": "assets/tennis_court_clay.jpg",
            "grass": "assets/tennis_court_grass.jpg",
        }

    def create(self, court_type="hard"):
        self.court_type = court_type

        # Create 3D scene
        self.scene = canvas(
            title=f"Tennis Court ({court_type.capitalize()})",
            width=800,
            height=600,
            center=vector(0, 0, 0),
            background=color.black,
        )

        # Lighting
        distant_light(direction=vector(0, 1, 0), color=color.white * 0.1)

        # Court
        self.court = box(
            pos=vector(0, 0, 0),
            size=vector(self.image.x, 0.1, self.image.z),
            texture=self.court_textures[self.court_type],
        )

        # Net and supports
        self.net = box(
            pos=vector(0, 0.5, 0),
            size=vector(0.1, 1, 12.3),
            color=color.white,
            opacity=0.4,
        )

        self.net_top = box(
            pos=vector(0, 0.98, 0),
            size=vector(0.11, 0.05, 12.3),
            color=color.white,
        )

        self.net_stand_center = box(
            pos=vector(0, 0.5, 0),
            size=vector(0.1, 1, 0.1),
            color=color.white,
        )

        self.net_stand_left = box(
            pos=vector(0, 0.5, self.stand_z),
            size=vector(0.2, 1.1, 0.2),
            color=color.black,
        )

        self.net_stand_right = box(
            pos=vector(0, 0.5, -self.stand_z),
            size=vector(0.2, 1.1, 0.2),
            color=color.black,
        )

        # Example balls
        self.ball = sphere(
            pos=vector(self.court_xz.x, 1.1, self.court_xz.z),
            radius=0.1,
            color=color.yellow,
        )

    def wait(self):
        input("Press Enter to exit...")

    def reset(self):
        pass


if __name__ == "__main__":
    pass
