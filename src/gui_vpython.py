from vpython import (
    canvas,
    box,
    color,
    vector,
    sphere,
    distant_light,
    rate,
    wtext,
    local_light,
    label,
    menu,
)
from types import SimpleNamespace
from src.engine import coordinates

"""
This module manages the court GUI and animations.

The actual computation should go into dynamics.py. This module should be able to
take the data from dynamics.py and apply a slow-motion algorithm by linearizing subsequent points.

TO DO:
- GUI with buttons: next point, previous point, select tournament, select match, slowmotion
- Actual animation loop
- Slowmotion
- Wrapper functions to the GUI elements
- Improve lighting (day/night) and camera (fix above surface)
- Improve court render (correct size, court types)
- Improve net render (curved net)
- Improve ball render (spin, trail, and mash)
"""
# Available court textures
COURT_TEXTURES = {
    "hard": "assets/tennis_court_background.jpg",
    "clay": "assets/tennis_court_clay.jpg",
    "grass": "assets/tennis_court_grass.jpg",
}


class GUI:
    """
    This class defines the canva and the GUI buttons.
    """

    def __init__(self):
        """
        Creates the GUI and scene.
        """
        self.scene_width = 1000

        self.court = TennisCourt()
        self.bg_color = color.black
        self.title = ""
        self.p1 = ""
        self.p2 = ""
        self.k = 1  # Slow motion parameter

    def create(self, t_list):
        # Create 3D scene
        self.scene = canvas(
            title=self.title,
            width=self.scene_width,
            height=self.scene_width * 10 // 20,
            center=vector(0, 3, 0),
            background=self.bg_color,
            resizable=False,
            autoscale=False,
        )

        # Menu and buttons
        self.tournament_menu = menu(
            bind=self.tournament_binder, choices=t_list, selected=t_list[0]
        )
        self.match_menu = menu(bind=self.match_binder, choices=[""], selected="")

        # Initialize console
        wtext(text="\n\n<b>CONSOLE</b>\n\n")
        self.console = wtext(text="\n\n")

        # Create court
        self.court.create(self.scene, self.p1, self.p2)

    def wait(self):
        input("Press Enter to exit...")

    def set_default_tournament(self, t_default):
        """
        Set default tournament
        """
        self.tournament_menu.selected = t_default

    def GUI_print(self, text, max_lines=10):
        """
        Print text to the GUI console, keeping only the last max_lines entries.
        """
        new_line = f"CONSOLE: {text}"

        lines = self.console.text.splitlines()
        lines.insert(0, new_line)

        self.console.text = "\n".join(lines[:max_lines]) + "\n"

    def bind_GUI(self, tournament_binder, match_binder):
        """
        Exposes the GUI bindings to the SIM side.
        """
        self.tournament_binder_sim = tournament_binder
        self.match_binder_sim = match_binder

    def tournament_binder(self, menu):
        """
        Wrapper function for the menu function.
        """
        val = menu.selected
        match_list = self.tournament_binder_sim(val)
        self.match_menu.choices = match_list

    def match_binder(self, menu):
        val = menu.selected
        match_data = self.match_binder_sim(val)

    def update_match_data(self, p1, p2, match):
        """
        Update the match data: title and labels
        """
        space = " " * (self.scene_width // 12)
        self.title = (
            f"\n<div style='width: {self.scene_width}px; text-align: center;'>"
            f"<b>{match} - {p1} vs {p2}\nFinal</b>"
            "</div>\n\n"
        )
        self.p1 = p1
        self.p2 = p2

        self.scene.title = self.title
        self.court.labelp1.text = self.p1
        self.court.labelp2.text = self.p2

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
        self.image = SimpleNamespace(x=25.9781, z=16.5201)
        self.court_xz, self.single_court, self.serve_box, _ = coordinates()
        self.stand_z = 6.15

        self.court_type = None
        self.day = False

    def create(self, scene, p1, p2, court_type="hard"):
        """
        Create the 3D scene and draw the tennis court.

        TO DO: if necessary, pass the scene as parameter and define scene in gui.py
        """
        # Attach to current scene
        self.court_type = court_type
        self.scene = scene
        self.scene.select()

        # Lighting
        distant_light(direction=vector(0, 1, 0), color=color.white * 0.1)

        # Court
        self.court = box(
            pos=vector(0, 0, 0),
            size=vector(self.image.x, 0.25, self.image.z),
            texture=COURT_TEXTURES[self.court_type],
        )

        # Net and supports
        self.net = box(
            pos=vector(0, 0.5, 0),
            size=vector(0.03, 1, 12.3),
            color=color.white,
            opacity=0.4,
        )

        self.net_band = box(
            pos=vector(0, 0.98, 0),
            size=vector(0.05, 0.05, 12.3),
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

        # Labels
        self.labelp1 = label(
            pos=vector(self.image.x / 2 - 2, 8, 0),
            text=p1,
            font="monospace",
            opacity=1,
            box=False,
            height=20,
        )
        self.labelp2 = label(
            pos=vector(-self.image.x / 2 + 2, 8, 0),
            text=p2,
            font="monospace",
            opacity=1,
            box=False,
            height=20,
        )

    def animate_trajectory(self, traj):
        """
        Animate the vPython ball along a NumPy trajectory array (N x 3).
        """
        if len(traj) > 0:
            s0 = traj[0]

            self.ball = sphere(
                pos=vector(float(s0[0]), float(s0[1]), float(s0[2])),
                radius=0.1,
                color=color.yellow,
                make_trail=True,
                trail_radius=0.05,
                retain=100,
            )
            for p in traj:
                rate(60)
                self.ball.pos = vector(float(p[0]), float(p[1]), float(p[2]))
                # self.ball.rotate(axis=vector(0,0,1), angle=0.5)
