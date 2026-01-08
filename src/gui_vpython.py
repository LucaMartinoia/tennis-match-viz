from vpython import (
    canvas,
    box,
    color,
    vector,
    sphere,
    local_light,
    rate,
    wtext,
    label,
    menu,
    button,
    slider,
    checkbox,
    bumpmaps,
)
from types import SimpleNamespace
from src.engine import coordinates
from datetime import datetime
import numpy as np
import os

"""
This module manages the court GUI and animations.

TO DO:
- Improve net (curved net)
- Improve ball (spin)
- Improve court bumpmaps/lightings
"""

# Available court textures
COURT_TEXTURES = {
    "hard": "assets/tennis_court_hard.jpg",
    "clay": "assets/tennis_court_clay.jpg",
    "grass": "assets/tennis_court_grass.jpg",
}


class GUI:
    """
    This class defines the canva and the GUI.
    """

    def __init__(self, bus, tournament_default) -> None:
        """
        Creates the GUI and scene.
        """
        # Initialize Event bus
        self.bus = bus
        self.bus.subscribe("tournament-list-ready", self.fill_tournament_menu)
        self.bus.subscribe("tournament-list-ready", self.heartbeat)
        self.bus.subscribe("match-list-ready", self.update_match_menu)
        self.bus.subscribe("match-metadata-ready", self.update_match_metadata)
        self.bus.subscribe("console-print", self.GUI_print)
        self.bus.subscribe("update-score", self.update_score_table)
        self.bus.subscribe("trajectory-ready", self.run_point)
        self.bus.subscribe("play-toggle", self.play_toggle)
        self.bus.subscribe("point-data-ready", self.point_data)

        # Scene data
        self.scene_width = 1000
        self.bg_color = color.black
        self.day = True

        # Match data
        self.tournament_default = tournament_default
        self.title = "\n\n\n\n\n"
        self.p1 = "\t\t"
        self.p2 = "\t\t"
        self.winner = ""
        self.server = ""
        self.n_points = 0
        self.point = 0
        self.second = False
        self.ace = 0
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
            center=vector(0, 2, 0),
            forward=vector(0, -0.5, 1),
            background=self.bg_color,
            resizable=False,
            autoscale=False,
        )

        # Lighting
        self.lights(self.day)

        # Bind ESC to quit program
        self.scene.bind("keydown", self.exit_program)
        self.scene.append_to_title(" " * 186 * (self.scene_width // 1000))
        self.button_exit = button(
            text="Exit ✖", bind=self.exit_program, pos=self.scene.title_anchor
        )

        # Create court
        self.court = TennisCourt(self.scene, self.p1, self.p2)

        # Empty score table
        self.score = wtext(
            text=f"""
            <div style='width: {self.scene_width}px; text-align: center; margin-top: -50; margin-bottom: -35; padding: 0;'>
                <table style='border-collapse: collapse; margin: 0 auto; font-size:16px; table-layout: fixed;'>
                    <tr>
                        <td style='width:24px;'></td>
                        <td style='border:none;padding:6px;'></td>
                        <td style='border:1px solid white;padding:6px;'>Set</td>
                        <td style='border:1px solid white;padding:6px;'>Game</td>
                        <td style='border:1px solid white;padding:6px;'>Point</td>
                    </tr>
                    <tr>
                        <td style='width:24px;text-align:center;border:none;'> </td>
                        <td style='border:1px solid white;padding:6px;'>{self.p1}</td>
                        <td style='border:1px solid white;padding:6px;'>{self.set1}</td>
                        <td style='border:1px solid white;padding:6px;'>{self.game1}</td>
                        <td style='border:1px solid white;padding:6px;'>{self.point1}</td>
                    </tr>
                    <tr>
                        <td style='width:24px;text-align:center;border:none;'> </td>
                        <td style='border:1px solid white;padding:6px;'>{self.p2}</td>
                        <td style='border:1px solid white;padding:6px;'>{self.set2}</td>
                        <td style='border:1px solid white;padding:6px;'>{self.game2}</td>
                        <td style='border:1px solid white;padding:6px;'>{self.point2}</td>
                    </tr>
                </table>
                <hr style='border:1px solid white; width:80%; margin: -15px auto 0 auto;'/>
            </div>
            """
        )

        #######################
        # Menu and buttons
        #######################

        # Play/Pause
        self.scene.append_to_caption("\t\t\t\t")
        self.button_play = button(bind=self.play_toggle, text="")
        if self.court.play:
            self.button_play.text = "    Play ▷ "
        else:
            self.button_play.text = " Pause ❚❚ "
        # Slowmotion slider
        self.scene.append_to_caption("\t\tBall speed: 1%")
        self.slider_slowmotion = slider(
            bind=self.slowmotion, min=1, max=100, value=100, length=200
        )
        self.scene.append_to_caption("100%")
        # Dark/light button switch
        self.scene.append_to_caption("\t\t")
        self.checkbox_night = checkbox(bind=self.day_toggle, text="Night mode")
        if self.day:
            self.checkbox_night.checked = False
        else:
            self.checkbox_night.checked = True
        # Tournament menu
        self.scene.append_to_caption("\n\n\tSelect match:\t\t")
        self.menu_tournament = menu(
            bind=self.tournament_binder, choices=[""], selected=""
        )
        # Match menu
        self.menu_match = menu(bind=self.match_binder, choices=[""], selected="")
        # First point button
        self.scene.append_to_caption("\n\n\tSelect point:\t\t")
        self.button_first = button(bind=self.change_point, text=" ⏮ ")
        self.scene.append_to_caption(" ")
        # Next point button
        self.button_next = button(bind=self.change_point, text=" ◀ ")
        self.scene.append_to_caption("\t")
        # Previous point button
        self.button_previous = button(bind=self.change_point, text=" ▶ ")
        self.scene.append_to_caption(" ")
        # Previous point button
        self.button_last = button(bind=self.change_point, text=" ⏭ ")

        # Initialize console
        wtext(
            text=f"""
            <div style='width: {self.scene_width}px; text-align: left; padding: 0; margin: 0;'>
                <hr style='border:1px solid white; width:80%; margin: -15px auto -45px auto;'/>
            </div>
            """
        )
        wtext(text=f"\n\t<b>CONSOLE</b>\n\n")
        self.console = wtext(text="\n\n\t")
        self.GUI_print("Welcome to TennisPointVisualizer!")
        self.GUI_print("Press ESC or the Exit button to quit.")

    def exit_program(self, evt) -> None:
        """
        Program exit point.
        """
        # Check if called from button press or key press
        is_key_exit = hasattr(evt, "key") and evt.key in ("esc", "escape", "end")
        is_button_exit = hasattr(evt, "text") and evt.text == "Exit"

        if is_key_exit or is_button_exit:
            # Delete scene and close thread
            self.scene.delete()
            os._exit(0)

    def heartbeat(self, t_list=None) -> None:
        """
        Heartbeat to keep scene alive after animation has finished.
        """
        # Create a hidden sphere
        heart = sphere(
            pos=vector(0, -1, 0),
            radius=0.01,
            color=color.red,
            visible=False,
        )
        # Keep rotating the sphere once per second
        while True:
            rate(1)
            heart.rotate(axis=vector(0, 1, 0), angle=0.01, origin=vector(0, 0, 0))

    def play_toggle(self, evt=None) -> None:
        """
        Bind method for the Play/Pause button.
        """
        # Toggle Play and Pause
        self.court.play = not self.court.play
        self.button_play.text = "    Play ▷ " if self.court.play else " Pause ❚❚ "

    def day_toggle(self, evt) -> None:
        """
        Bind method for the light/dark mode switch.
        """
        flag = False if evt.checked else True
        self.lights(flag)

    def lights(self, day_flag: bool) -> None:
        """
        Method to set light/dark mode.
        """
        # Reset lights
        self.scene.lights = []
        if day_flag:
            # Bright ambient light, no lightings
            self.scene.background = color.white
            self.scene.ambient = color.white * 1
        else:
            # Dim ambient light, local lights
            self.scene.background = color.black
            self.scene.ambient = color.white * 0.05
            local_light(pos=vector(18, 8, -8), color=color.white * 0.25)
            local_light(pos=vector(-18, 8, -8), color=color.white * 0.25)
            local_light(pos=vector(-18, 8, 8), color=color.white * 0.25)
            local_light(pos=vector(18, 8, 8), color=color.white * 0.25)
            local_light(pos=vector(0, 8, 8), color=color.white * 0.25)
            local_light(pos=vector(0, 8, -8), color=color.white * 0.25)

    def slowmotion(self, evt) -> None:
        """
        Bind method for the slowmotion slider.
        """
        self.court.rate = self.slider_slowmotion.value

    def change_point(self, evt) -> None:
        """
        Bind method for the change point buttons.
        """
        # Emit signal "change-point"
        if evt.text == " ⏮ ":
            self.bus.emit("change-point", point="first")
        elif evt.text == " ◀ ":
            self.bus.emit("change-point", point="previous")
        elif evt.text == " ▶ ":
            self.bus.emit("change-point", point="next")
        elif evt.text == " ⏭ ":
            self.bus.emit("change-point", point="last")

    def point_data(self, data) -> None:
        """
        Callback to set the point data.
        """
        self.point, self.second, self.ace, self.winner = data

    def update_score_table(self, score) -> None:
        """
        Bind method for the "update-score" signal.

        Update the score table.
        """
        (
            self.set1,
            self.set2,
            self.game1,
            self.game2,
            self.point1,
            self.point2,
            self.server,
        ) = score
        dot = ["", ""]
        if self.server == 1:
            dot[0] = "●"
        elif self.server == 2:
            dot[1] = "●"

        self.score.text = f"""
            <div style='width: {self.scene_width}px; text-align: center; margin-top: -50; margin-bottom:-35; padding: 0;'>
                <table style='border-collapse: collapse; margin: 0 auto; font-size:16px; table-layout: fixed;'>
                    <tr>
                        <td style='width:24px;'></td>
                        <td style='border:none;padding:6px;'></td>
                        <td style='border:1px solid white;padding:6px;'>Set</td>
                        <td style='border:1px solid white;padding:6px;'>Game</td>
                        <td style='border:1px solid white;padding:6px;'>Point</td>
                    </tr>
                    <tr>
                        <td style='width:24px;text-align:center;border:none;'>{dot[0]}</td>
                        <td style='border:1px solid white;padding:6px;'>{self.p1}</td>
                        <td style='border:1px solid white;padding:6px;'>{self.set1}</td>
                        <td style='border:1px solid white;padding:6px;'>{self.game1}</td>
                        <td style='border:1px solid white;padding:6px;'>{self.point1}</td>
                    </tr>
                    <tr>
                        <td style='width:24px;text-align:center;border:none;'>{dot[1]}</td>
                        <td style='border:1px solid white;padding:6px;'>{self.p2}</td>
                        <td style='border:1px solid white;padding:6px;'>{self.set2}</td>
                        <td style='border:1px solid white;padding:6px;'>{self.game2}</td>
                        <td style='border:1px solid white;padding:6px;'>{self.point2}</td>
                    </tr>
                </table>
                <hr style='border:1px solid white; width:80%; margin: -15px auto 0 auto;'/>
            </div>
            """

    def fill_tournament_menu(self, t_list) -> None:
        """
        Set the tournament list in the menu.
        """
        # Set the tournament choices and selected entry
        self.menu_tournament.choices = t_list
        if self.tournament_default in t_list:
            self.menu_tournament.selected = self.tournament_default
        else:
            self.menu_tournament.selected = t_list[0]
        # Manual call of the binders on creation
        self.tournament_binder(self.menu_tournament)

    def set_default_tournament(self, t_default) -> None:
        """
        Set default tournament. TO DO
        """
        self.menu_tournament.selected = t_default

    def GUI_print(self, text: str, max_lines=10) -> None:
        """
        Print text to the GUI console, keeping only the last max_lines entries.
        """
        ts = datetime.now().strftime("%H:%M:%S")
        new_line = f"\t[{ts}]: {text}"

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

    def update_match_metadata(self, metadata) -> None:
        """
        Update the match data (title and labels).
        """
        # Gather match metadata
        self.p1, self.p2, match, tournament, self.n_points, court = metadata
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
        self.scene.append_to_title(" " * 186 * (self.scene_width // 1000))
        self.button_exit = button(
            text="Exit ✖", bind=self.exit_program, pos=self.scene.title_anchor
        )
        # Set court texture
        self.court.court.texture = COURT_TEXTURES[court]

    def run_point(self, traj) -> None:
        """
        Wrapper function to animate_trajectory.
        """
        # Increase animation id counter
        self.court.anim_id += 1
        current_id = self.court.anim_id
        # If not already animating, animate the point
        if not self.court.animating:
            finished = self.court._animate_trajectory(traj, current_id)
            # Emit when finished
            if finished:
                self.bus.emit("animation-finished")
            else:
                # If it does not work, emit to ask the current trajectory
                self.bus.emit("animation-interrupted")


class TennisCourt:
    """
    Animate the court and the ball.
    """

    def __init__(self, scene, p1: str, p2: str, court_type="grass") -> None:
        """
        Take the scene from GUI and draw the tennis objects.
        """
        # Dimensions in meters (scaled to include surroundings)
        self.image = SimpleNamespace(
            x=40.6, z=19.2  # x=25.9781, z=16.5201 or x=40.6, z=19.2
        )
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

        # Court
        self.court = box(
            pos=vector(0, 0, 0),
            size=vector(self.image.x, 0.25, self.image.z),
            texture={
                "file": COURT_TEXTURES[self.court_type],
                # "bumpmap": bumpmaps.gravel,
            },
            shininess=0.1,
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
            texture={"file": "assets/ball.jpg"},
            pos=vector(0, 0, 0),
            radius=0.08,
            color=color.white,
            make_trail=False,
            trail_radius=0.03,
            trail_color=color.yellow,
            retain=3,
            visible=False,
        )

        # Player labels
        self.labelp1 = label(
            pos=vector(self.single_court.x + 1, 8, 0),
            text=p1,
            font="monospace",
            opacity=1,
            box=False,
            height=20,
        )
        self.labelp2 = label(
            pos=vector(-self.single_court.x - 1, 8, 0),
            text=p2,
            font="monospace",
            opacity=1,
            box=False,
            height=20,
        )

        # Info label
        self.info = label(
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
                        self.info.text = "First serve" if i <= 100 else "Second serve"
                        self.info.visible = True
                    else:
                        self.ball.visible = True
                        self.ball.make_trail = True
                        self.info.text = ""
                        self.info.visible = False
                    # Update ball position
                    self.ball.pos = vector(float(p[0]), float(p[1]), float(p[2]))
                    self.ball.rotate(axis=vector(0, 0, 1), angle=0.5)
                    i += 1
        self.animating = False
        return True
