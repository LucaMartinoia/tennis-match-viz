from vpython import canvas, box, color, vector, sphere, distant_light, rate
from types import SimpleNamespace
from src.engine import coordinates

"""
This module manages the court GUI and animations.

The actual computation should go into dynamics.py. This module should be able to
take the data from dynamics.py and apply a slow-motion algorithm by linearizing subsequent points.
"""


class GUI:
    """
    This class defines the canva and the GUI buttons.
    """

    def __init__(self):
        """
        Creates the scene.
        """
        self.animation_speed = 1  # TO DO: slowmotion parameter
        pass

    # BUTTONS: tournament/match selector, animation speed, arrows to move between points inside the same match.


class TennisCourt:
    """
    All the bits to animate the court and the ball.
    """

    def __init__(self):
        """
        Takes as input the scene from GUI and append the actual tennis objects.
        """
        # Dimensions in meters (scaled to include surroundings)
        self.image = SimpleNamespace()
        self.image.x = 25.9781
        self.image.z = 16.5201

        self.court_xz, self.single_court, self.serve_box, net = coordinates()

        self.stand_z = 6.15

        self.scene = None
        self.court_type = None

        # Available court textures
        self.court_textures = {
            "hard": "assets/tennis_court_background.jpg",
            "clay": "assets/tennis_court_clay.jpg",
            "grass": "assets/tennis_court_grass.jpg",
        }

    def create(self, court_type="hard"):
        """
        Create the 3D scene and draw the tennis court.

        TO DO: if necessary, pass the scene as parameter and define scene in gui.py
        """
        self.court_type = court_type

        # Create 3D scene
        self.scene = canvas(
            title=f"Tennis Court ({court_type.capitalize()})",
            width=800,
            height=600,
            center=vector(0, 0, 0),
            background=color.black,
        )
        self.scene.autoscale = False

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

    def wait(self):
        input("Press Enter to exit...")

    def point(self, point_data, serve=False):
        """
        This function should just take as input the point positions and draw them.
        """
        pass

    def animate_trajectory(self, traj):
        """
        Animate the VPython ball along a NumPy trajectory array (N x 3).
        """
        s0 = traj[0]
        self.ball = sphere(
            pos=vector(float(s0[0]), float(s0[1]), float(s0[2])),
            radius=0.1,
            color=color.yellow,
            make_trail=True,
            retain=500,
        )
        for p in traj:
            rate(30)
            self.ball.pos = vector(float(p[0]), float(p[1]), float(p[2]))

        self.wait()
