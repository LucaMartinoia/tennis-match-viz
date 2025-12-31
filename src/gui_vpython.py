from vpython import (
    canvas,
    box,
    color,
    vector,
    sphere,
    distant_light,
    rate,
    wtext,
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
    This class defines the canva and the GUI.
    """

    def __init__(self, bus) -> None:
        """
        Creates the GUI and scene.
        """
        # Bus initialization and subscriptions
        self.bus = bus
        self.bus.subscribe("tournament-list-ready", self.fill_tournament_menu)
        self.bus.subscribe("matches-ready", self.update_match_menu)
        self.bus.subscribe("match-metadata-ready", self.update_match_data)
        self.bus.subscribe("console-print", self.GUI_print)
        self.bus.subscribe("update-score", self.update_score_table)
        self.bus.subscribe("trajectory-ready", self.run_point)
        self.bus.subscribe("play-toggle", self.play_toggle)

        # Scene data
        self.scene_width = 1000
        self.bg_color = color.black

        # Match data
        self.title = "\n\n\n\n\n\n\n"
        self.p1 = "\t\t"
        self.p2 = "\t\t"
        self.set1 = 0
        self.set2 = 0
        self.game1 = 0
        self.game2 = 0
        self.point1 = 0
        self.point2 = 0

        # Create scene
        self.scene = canvas(
            title=self.title,
            width=self.scene_width,
            height=self.scene_width * 10 // 20,
            center=vector(0, 8, 0),
            background=self.bg_color,
            resizable=False,
            autoscale=False,
        )

        # Bind ESC to quit program
        self.scene.bind("keydown", self.exit_program)
        self.button_exit = button(
            text="Exit", bind=self.exit_program, pos=self.scene.title_anchor
        )

        # Create court
        self.court = TennisCourt(self.scene, self.p1, self.p2)

        # Empty score table
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
        # Tournament menu
        self.menu_tournament = menu(
            bind=self.tournament_binder, choices=[""], selected=""
        )
        # Match menu
        self.menu_match = menu(bind=self.match_binder, choices=[""], selected="")
        self.scene.append_to_caption("\t\t")
        # Play/Pause button
        self.button_play = button(bind=self.play_toggle, text="")
        if self.court.play:
            self.button_play.text = " Play ▶ "
        else:
            self.button_play.text = " Pause ❚❚ "
        self.scene.append_to_caption("\t\t")
        # Next point button
        self.button_next = button(bind=self.change_point, text=" ⇦ ")
        self.scene.append_to_caption(" ")
        # Previous point button
        self.button_next = button(bind=self.change_point, text=" ⇨ ")

        # Initialize console
        wtext(text="\n\n<b>CONSOLE</b>\n\n")
        self.console = wtext(text="\n\n")
        wtext(text="Press ESC or the Exit button to quit.\n\n")

    def exit_program(self, evt) -> None:
        """
        Main exit point.
        """
        # Check if called from button press or key press
        is_key_exit = hasattr(evt, "key") and evt.key in ("esc", "escape", "end")
        is_button_exit = hasattr(evt, "text") and evt.text == "Exit"

        if is_key_exit or is_button_exit:
            # Delete scene and close thread
            self.scene.delete()
            os._exit(0)

    def play_toggle(self, evt=None) -> None:
        """
        Bind method for the Play/Pause button.
        """
        # Toggle Play and Pause
        print(f"reading play-toggle {not self.court.play}")
        self.court.play = not self.court.play
        self.button_play.text = " Play ▶ " if self.court.play else " Pause ❚❚ "

    def change_point(self, evt) -> None:
        """
        Bind method for the change point buttons.
        """
        # Emit signal "change-point"
        if evt.text == " ⇦ ":
            self.bus.emit("change-point", next=False)
        else:
            self.bus.emit("change-point", next=True)

    def update_score_table(self, score) -> None:
        """
        Bind method for the "update-score" signal.

        Update the score table.
        """
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

    def fill_tournament_menu(self, t_list) -> None:
        """
        Set the tournament list in the menu.
        """
        # Set the tournament choices and selected entry
        self.menu_tournament.choices = t_list
        self.menu_tournament.selected = t_list[0]
        # Manual call of the binders on creation
        self.tournament_binder(self.menu_tournament)

    def set_default_tournament(self, t_default):
        """
        Set default tournament.
        """
        self.menu_tournament.selected = t_default

    def GUI_print(self, text: str, max_lines=10) -> None:
        """
        Print text to the GUI console, keeping only the last max_lines entries.
        """
        ts = datetime.now().strftime("%H:%M:%S")
        new_line = f"[{ts}] CONSOLE: {text}"

        lines = self.console.text.splitlines()
        lines.insert(0, new_line)

        self.console.text = "\n".join(lines[:max_lines]) + "\n"

    def tournament_binder(self, menu) -> None:
        """
        Bind method for the tournament menu.
        """
        # Emit signal on the bus to start gathering match data
        self.bus.emit("tournament-selected", tournament=menu.selected)

    def update_match_menu(self, matches) -> None:
        """
        Method that sets data in the match menu.
        """
        # Initialize the menu
        self.menu_match.choices = matches
        self.menu_match.selected = matches[0]

    def match_binder(self, menu) -> None:
        """
        Bind method for the match menu.
        """
        # Emit signal on the bus to start computing point data
        self.bus.emit("match-selected", match_name=menu.selected)

    def update_match_data(self, metadata) -> None:
        """
        Update the match data (title and labels).
        """
        # Gather match metadata
        self.p1, self.p2, match, tournament = metadata
        # Set the title
        self.title = (
            f"\n<div style='width: {self.scene_width}px; text-align: center;font-size:18px;'>"
            f"<b>{tournament}\n{match}</b>"
            "</div>\n"
        )
        self.scene.title = self.title
        # Set scene labels
        self.court.labelp1.text = self.p1
        self.court.labelp2.text = self.p2
        # Recreate the exit button
        self.button_exit = button(
            text="Exit", bind=self.exit_program, pos=self.scene.title_anchor
        )

    def run_point(self, traj) -> None:
        """
        Wrapper function to animate_trajectory.
        """
        self.court.anim_id += 1
        current_id = self.court.anim_id
        # Animate the point
        if not self.court.animating:
            finished = self.court._animate_trajectory(traj, current_id)
            # When finished, call next point
            # self.wait()
            if finished:
                self.bus.emit("animation-finished")
            else:
                # If it does not work, emit to ask the current trajectory
                self.bus.emit("animation-interrupted")
        # If the program quits on last point,
        # try to have an emit from match and if match_point ->"pause".

    def wait(self) -> None:
        input("Press Enter to exit...")


class TennisCourt:
    """
    Animate the court and the ball.
    """

    def __init__(self, scene, p1: str, p2: str, court_type="hard") -> None:
        """
        Take the scene from GUI and draw the tennis objects.
        """
        # Dimensions in meters (scaled to include surroundings)
        self.image = SimpleNamespace(
            x=25.9781, z=16.5201
        )  # TODO: Dictionary based on court_type
        self.court_xz, self.single_court, self.serve_box, _ = coordinates()
        self.stand_z = 6.15

        self.court_type = court_type
        self.day = False

        self.rate = 100  # Slow motion parameter
        self.play = False  # Pause/Play flag
        self.animating = False
        self.anim_id = 0

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

        # Ball
        self.ball = sphere(
            pos=vector(0, 0, 0),
            radius=0.06,
            color=color.yellow,
            make_trail=False,
            trail_radius=0.03,
            retain=3,
            visible=False,
        )

        # Player labels
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

        # Serve label
        self.serve = label(
            text="",
            pos=vector(0, 10, 0),
            visible=False,
            align="center",
            font="monospace",
            opacity=1,
            box=False,
            height=25,
        )

    def _animate_trajectory(self, traj, anim_id) -> bool:
        """
        Animate the ball along a NumPy trajectory array (N x 3).
        """
        # Initialize the ball position and make it visible
        if len(traj) > 0:
            self.animating = True
            s0 = traj[0]
            self.ball.pos = vector(s0[0], s0[1], s0[2])
            self.ball.clear_trail()
            self.ball.visible = True
            self.ball.make_trail = True
            # Loop over trajectory points
            i = 0
            while i < len(traj):
                rate(self.rate)

                # Cancellation check
                if anim_id != self.anim_id:
                    self.animating = False
                    return False

                if self.play:
                    p = traj[i]
                    # If p is NAN, hide ball and show serve label
                    if np.isnan(p[0]):
                        self.ball.clear_trail()
                        self.ball.visible = False
                        self.ball.make_trail = False
                        self.serve.text = "First serve" if i <= 100 else "Second serve"
                        self.serve.visible = True
                    else:
                        self.ball.visible = True
                        self.ball.make_trail = True
                        self.serve.text = ""
                        self.serve.visible = False
                    # Update ball position
                    self.ball.pos = vector(float(p[0]), float(p[1]), float(p[2]))
                    i += 1
                    # self.ball.rotate(axis=vector(0,0,1), angle=0.5)
        self.animating = False
        return True
