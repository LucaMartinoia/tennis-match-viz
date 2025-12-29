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
    button,
)
from types import SimpleNamespace
from src.engine import coordinates
from datetime import datetime
import numpy as np
import os

"""
This module manages the court GUI and animations.

The actual computation should go into dynamics.py. This module should be able to
take the data from dynamics.py and apply a slow-motion algorithm by linearizing subsequent points.

TO DO:
- Slowmotion
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

    def __init__(self, bus):
        """
        Creates the GUI and scene.
        """
        # Bus subscriptions
        self.bus = bus
        self.bus.subscribe("matches_updated", self.update_match_menu)
        self.bus.subscribe("match_metadata_updated", self.update_match_data)
        self.bus.subscribe("console-print", self.GUI_print)
        self.bus.subscribe("update-score", self.update_score_table)
        self.bus.subscribe("trajectory", self.run_point)

        # Scene data
        self.scene_width = 1000
        self.bg_color = color.black

        # Match data
        self.title = "\n\n\n\n\n\n"
        self.p1 = ""
        self.p2 = ""
        self.set1 = 0
        self.set2 = 0
        self.game1 = 0
        self.game2 = 0
        self.point1 = 0
        self.point2 = 0

        # Create 3D scene
        self.scene = canvas(
            title=self.title,
            width=self.scene_width,
            height=self.scene_width * 10 // 20,
            center=vector(0, 8, 0),
            background=self.bg_color,
            resizable=False,
            autoscale=False,
        )
        self.scene.bind("keydown", self.exit_program)

        # Create court
        self.court = TennisCourt(self.scene, self.p1, self.p2)
        self.scene.append_to_caption("\n")
        self.score = wtext(
            text=f"<div style='width: {self.scene_width}px; text-align: left;'>"
            "<table style='border-collapse:collapse;margin-left:0;margin-right:auto;font-size:16px;'>"
            "<tr>"
            "<td style='border:1px solid white;padding:6px;'>Player</td>"
            "<td style='border:1px solid white;padding:6px;'>Set</td>"
            "<td style='border:1px solid white;padding:6px;'>Game</td>"
            "<td style='border:1px solid white;padding:6px;'>Point</td>"
            "</tr>"
            "<tr>"
            f"<td style='border:1px solid white;padding:6px;'>{self.p1}</td>"
            f"<td style='border:1px solid white;padding:6px;'>{self.set1}</td>"
            f"<td style='border:1px solid white;padding:6px;'>{self.game1}</td>"
            f"<td style='border:1px solid white;padding:6px;'>{self.point1}</td>"
            "</tr>"
            "<tr>"
            f"<td style='border:1px solid white;padding:6px;'>{self.p2}</td>"
            f"<td style='border:1px solid white;padding:6px;'>{self.set2}</td>"
            f"<td style='border:1px solid white;padding:6px;'>{self.game2}</td>"
            f"<td style='border:1px solid white;padding:6px;'>{self.point2}</td>"
            "</tr>"
            "</table>"
            "</div>\n"
        )

        # Menu and buttons
        self.menu_tournament = menu(
            bind=self.tournament_binder, choices=[""], selected=""
        )
        self.menu_match = menu(bind=self.match_binder, choices=[""], selected="")
        self.scene.append_to_caption("\t\t")
        self.button_play = button(bind=self.start_toggle, text=" ▶ ")
        self.scene.append_to_caption("\t\t")
        self.button_next = button(bind=self.previous_point, text=" ⇦ ")
        self.scene.append_to_caption(" ")
        self.button_next = button(bind=self.next_point, text=" ⇨ ")

        # Initialize console
        wtext(text="\n\n<b>CONSOLE</b>\n\n")
        self.console = wtext(text="\n\n")
        self.GUI_print("Press ESC or the Exit button to quit.")

    def wait(self):
        input("Press Enter to exit...")

    def exit_program(self, evt):
        """
        Main exit point.
        """
        is_key_exit = hasattr(evt, "key") and evt.key in ("esc", "escape", "end")
        is_button_exit = hasattr(evt, "text") and evt.text == "Exit"

        if is_key_exit or is_button_exit:
            self.scene.delete()
            os._exit(0)

    def start_toggle(self):
        self.court.play = not self.court.play
        self.button_play.text = " ▶ " if self.court.play else " ❚❚ "

    def next_point(self):
        self.bus.emit("change-point", next=True)

    def previous_point(self):
        self.bus.emit("change-point", next=False)

    def update_score_table(self, score):
        self.set1, self.set2, self.game1, self.game2, self.point1, self.point2 = score
        self.score.text = (
            f"<div style='width: {self.scene_width}px; text-align: left;'>"
            "<table style='border-collapse:collapse;margin-left:0;margin-right:auto;font-size:16px;'>"
            "<tr>"
            "<td style='border:1px solid white;padding:6px;'>Player</td>"
            "<td style='border:1px solid white;padding:6px;'>Set</td>"
            "<td style='border:1px solid white;padding:6px;'>Game</td>"
            "<td style='border:1px solid white;padding:6px;'>Point</td>"
            "</tr>"
            "<tr>"
            f"<td style='border:1px solid white;padding:6px;'>{self.p1}</td>"
            f"<td style='border:1px solid white;padding:6px;'>{self.set1}</td>"
            f"<td style='border:1px solid white;padding:6px;'>{self.game1}</td>"
            f"<td style='border:1px solid white;padding:6px;'>{self.point1}</td>"
            "</tr>"
            "<tr>"
            f"<td style='border:1px solid white;padding:6px;'>{self.p2}</td>"
            f"<td style='border:1px solid white;padding:6px;'>{self.set2}</td>"
            f"<td style='border:1px solid white;padding:6px;'>{self.game2}</td>"
            f"<td style='border:1px solid white;padding:6px;'>{self.point2}</td>"
            "</tr>"
            "</table>"
            "</div>\n"
        )

    def set_tournament_menu(self, t_list):
        """
        Set the tournament list in the menu.
        """
        self.menu_tournament.choices = t_list
        self.menu_tournament.selected = t_list[0]
        # Manual call of the binders on creation
        self.tournament_binder(self.menu_tournament)

    def set_default_tournament(self, t_default):
        """
        Set default tournament
        """
        self.menu_tournament.selected = t_default

    def GUI_print(self, text, max_lines=10):
        """
        Print text to the GUI console, keeping only the last max_lines entries.
        """
        ts = datetime.now().strftime("%H:%M:%S")
        new_line = f"[{ts}] CONSOLE: {text}"

        lines = self.console.text.splitlines()
        lines.insert(0, new_line)

        self.console.text = "\n".join(lines[:max_lines]) + "\n"

    def tournament_binder(self, menu):
        """
        Wrapper function for the tournament menu.
        """
        tournament = menu.selected
        self.bus.emit("tournament_selected", tournament=tournament)

    def update_match_menu(self, matches):
        """
        Wrapper function that subscribes to update match events.
        """
        self.menu_match.choices = matches
        self.menu_match.selected = matches[0]

    def match_binder(self, menu):
        """
        Wrapper function for the match menu.
        """
        match_name = menu.selected
        self.bus.emit("match_selected", match_name=match_name)

    def update_match_data(self, metadata):
        """
        Update the match data: title and labels
        """
        p1, p2, match, tournament = metadata
        self.title = (
            f"\n<div style='width: {self.scene_width}px; text-align: center;font-size:18px;'>"
            f"<b>{tournament}\n{match}</b>"
            "</div>\n"
        )
        self.p1 = p1
        self.p2 = p2

        self.scene.title = self.title
        self.court.labelp1.text = self.p1
        self.court.labelp2.text = self.p2

        self.exit_button = button(
            text="Exit", bind=self.exit_program, pos=self.scene.title_anchor
        )

    def run_point(self, traj):
        """
        Wrapper function for the animate_trajectory.
        """
        self.court.animate_trajectory(traj)

        self.next_point()
        # If the program quits on last point,
        # try to have an emit from match and if match_point ->"pause".


class TennisCourt:
    """
    All the bits to animate the court and the ball.
    """

    def __init__(self, scene, p1, p2, court_type="hard"):
        """
        Takes as input the scene from GUI and append the actual tennis objects.
        """
        # Dimensions in meters (scaled to include surroundings)
        self.image = SimpleNamespace(x=25.9781, z=16.5201)
        self.court_xz, self.single_court, self.serve_box, _ = coordinates()
        self.stand_z = 6.15

        self.court_type = court_type
        self.day = False

        self.k = 1  # Slow motion parameter
        self.play = True

        # Attach to current scene
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

        self.ball = sphere(
            pos=vector(0, 0, 0),
            radius=0.1,
            color=color.yellow,
            make_trail=False,
            trail_radius=0.03,
            retain=10,
            visible=False,
        )
        self.serve = label(
            text="Second serve",
            pos=vector(0, 10, 0),
            visible=False,
            align="center",
            font="monospace",
            opacity=1,
            box=False,
            height=25,
        )

    def animate_trajectory(self, traj):
        """
        Animate the vPython ball along a NumPy trajectory array (N x 3).
        """
        if len(traj) > 0:
            s0 = traj[0]
            self.ball.pos = vector(s0[0], s0[1], s0[2])
            self.ball.visible = True

            i = 0
            while i < len(traj):
                rate(60)
                if self.play:
                    p = traj[i]
                    if np.isnan(p[0]):
                        self.ball.make_trail = False
                        self.serve.visible = True
                    else:
                        self.ball.make_trail = True
                        self.serve.visible = False
                    self.ball.pos = vector(float(p[0]), float(p[1]), float(p[2]))
                    i += 1
                    # self.ball.rotate(axis=vector(0,0,1), angle=0.5)
