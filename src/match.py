import numpy as np
from types import SimpleNamespace
from src.engine import Engine
from dataclasses import dataclass
import re

"""
This module manages the core logic: it takes the match database and,
for each point, computes the full trajectory of the ball.
"""


def coordinates():
    """
    Returns the x-z coordinates of various tennis court regions
    with respect to the origin at the center.
    """
    # Total length and width (doubles)
    court = SimpleNamespace(x=23.77 / 2, z=10.97 / 2)
    # Total length and width (single)
    single_court = SimpleNamespace(x=23.77 / 2, z=8.23 / 2)
    # Serve box length and width
    serve_box = SimpleNamespace(x=6.40, z=8.23 / 2)
    # Net height
    net = SimpleNamespace(center=0.915, sides=1.07)

    return court, single_court, serve_box, net


court, single_court, serve_box, net = coordinates()

# Constants
ERRORS_STR = ["n", "w", "d", "x", "g", "e"]  # Error code
# Court bbox
MODE_BBOX = SimpleNamespace(
    net=[0.15, -serve_box.z, 0.15, 0],
    serve=[-serve_box.x, -serve_box.z, 0, 0],
    single=[-single_court.x, -single_court.z, 0, single_court.z],  # net bbox
)
# Serve region bbox
SERVE_BBOX = SimpleNamespace(
    wide=[-serve_box.x, -serve_box.z, -serve_box.x + 2, -serve_box.z * 3 / 4],
    downT=[-serve_box.x, -serve_box.z * 1 / 3, -serve_box.x + 2, 0],
    body=[-serve_box.x, -serve_box.z * 3 / 4, -serve_box.x + 2, -serve_box.z * 1 / 3],
    all=[-serve_box.x, -serve_box.z, -serve_box.x + 2, 0],
)
# Single region bbox, TO DO
SINGLE_BBOX = SimpleNamespace(
    wide=[-serve_box.x, -serve_box.z, -serve_box.x + 2, -serve_box.z * 3 / 4],
    downT=[-serve_box.x, -serve_box.z * 1 / 3, -serve_box.x + 2, 0],
    body=[-serve_box.x, -serve_box.z * 3 / 4, -serve_box.x + 2, -serve_box.z * 1 / 3],
    all=[-serve_box.x, -serve_box.z, -serve_box.x + 2, 0],
)


@dataclass
class ShotIntent:
    x: float
    y: float
    z: float
    T: float
    net: bool = False


class Match:
    """
    The match class parses shot data into geometric quantities.
    """

    def __init__(self, df):
        """
        Loads the match data and keep track of points.
        """
        # Load the match dataframe
        print("Loading engine...")
        self.match_df = df
        self.point_in_game = 0  # To compute the quadrant of the server
        self.point = 1  # Point under consideration
        self.engine = Engine()  # One point per timestep

    def serve(self, serve_str: str) -> None:
        """
        Parse the serve string and compute the trajectory.
        """
        # Compute bbox
        serve_area = {
            "4": SERVE_BBOX.wide,
            "5": SERVE_BBOX.body,
            "6": SERVE_BBOX.downT,
        }.get(serve_str[0], SERVE_BBOX.all)

        # Find landing spot
        xf, zf = self.engine.random_point_in_bbox(serve_area)
        shot_data = ShotIntent(
            x=xf,
            y=0.05,
            z=zf,
            T=np.random.uniform(0.3, 0.4),
        )

        # If error, modify the landing spot
        if serve_str[-1] in ERRORS_STR:
            self.apply_error(shot_data, serve_str[-1], MODE_BBOX.serve)

        # Serve shot
        v_f = self.engine.serve(shot_data.x, shot_data.y, shot_data.z, shot_data.T)

        # If net, fall down to ground
        if shot_data.net:
            v_f = self.engine.net_drop()

        # Bounces
        if shot_data.net:
            n = 3
        elif "*" in serve_str or serve_str[-1] in ERRORS_STR:
            n = 2
        else:
            n = 1

        self.engine.bounces(v_f, n)

    def point_trajectory(self):
        """
        Extract the point data and call the serve and shot functions.
        """
        # Extract point data
        row = self.match_df.iloc[self.point - 1]

        first = row["1st"]
        second = row["2nd"]

        # First serve attempt
        if first:
            self._run_rally(first)

            # Check if first serve was a fault
            if second:
                self.engine.pause(1.0)
                self._run_rally(second)

        print("Trajectory computed successfully.")

    def _run_rally(self, rally):
        """
        Compute the rally trajectory.
        """
        # Call serve first, then the shots
        self.serve(rally[0])
        for shot in rally[1:]:
            self.shot(shot)

    def shot(self, shot_str: str) -> None:
        """
        This function takes the single shots and create the trajectory.

        [6b, b28f, f3b, b3b, b2f, f3b, b3d@] or [5b, b38s, s1w#]
        """
        m = re.match(r"^([A-Za-z])(\d{0,2})(.+)$", shot_str)  # Regex match
        if not m:
            raise ValueError(f"Invalid shot string: {shot_str}")

        shot_type, position, response = m.groups()
        l = len(shot_str)
        print(f"pattern: {shot_type}, {position}, {response}; length {l}")

        shot_z_bounds = {
            "1": SERVE_BBOX.wide,
            "2": SERVE_BBOX.body,
            "3": SERVE_BBOX.downT,
        }.get(shot_type, SERVE_BBOX.all)
        shot_x_bounds = {
            "4": SERVE_BBOX.wide,
            "5": SERVE_BBOX.body,
            "6": SERVE_BBOX.downT,
        }.get(shot_type, SERVE_BBOX.all)

        if position:
            pass

        # Determine time T based on shot type
        match shot_type:
            # TO DO: differentiate between shots
            case "f" | "b" | "r" | "s" | "t" | "q":
                T = np.random.uniform(0.3, 0.45)  # endline shots
            case "v" | "z" | "h" | "i" | "j" | "k":
                T = np.random.uniform(0.2, 0.35)  # voleè
            case "o" | "p":
                T = np.random.uniform(0.2, 0.35)  # smash
            case "u" | "y":
                T = np.random.uniform(0.6, 0.85)  # drop shot
            case "l" | "m":
                T = np.random.uniform(1, 1.5)  # lob
            case _:
                T = np.random.uniform(0.3, 0.45)  # fallback

    def _quadrant_selection(self, point, server):
        """
        This function takes the score and the server (p1 or p2)
        and computes the final trajectory.

        This is done via symmetry: if p2 is serving, the trajectory is symmetrized
        along the x axis. If the score is "odd", then the trajectory is symmetrized
        along the z axis.
        """
        pass

    def select_point(self, point: int) -> None:
        """
        Setter method for the point in the match.
        Also updates point_in_game.
        """
        # Assign new point
        self.point = point

        # Current games
        idx = self.point - 1
        gm1 = self.match_df.iloc[idx]["Gm1"]
        gm2 = self.match_df.iloc[idx]["Gm2"]

        # Find first point in the current game looping backward
        i = idx
        count = 0
        while (
            self.match_df.iloc[i - 1]["Gm1"] == gm1
            and self.match_df.iloc[i - 1]["Gm2"] == gm2
        ):
            count += 1
            i -= 1

        # 0-based count within the game
        self.point_in_game = count

    def reset_all(self) -> None:
        """
        Setter method for the point in the match.
        """
        self.point_in_game = 0  # To compute the quadrant of the server
        self.point = 1  # Point under consideration
        self.engine.reset()

    def apply_error(self, intent: ShotIntent, err: str, mode_bbox) -> None:
        """
        Apply error effects to a shot.
        """
        # Court parameters
        xmin, zmin, _, zmax = mode_bbox
        court_zmid = 0.5 * (mode_bbox[1] + mode_bbox[3])

        match err:
            case "n" | "g":  # Net or foot fault
                # Recompute all values
                intent.x, intent.z = self.engine.random_point_in_bbox(MODE_BBOX.net)
                intent.T = np.random.uniform(0.2, 0.35)
                intent.y = np.random.uniform(0.3, 0.91)
                intent.net = True

            case "w":  # Wide shot
                # Adjust position depending on theoretical position
                if intent.z < court_zmid:
                    zspan = intent.z - zmin
                    intent.z -= np.random.uniform(zspan, zspan + 1)
                else:
                    zspan = zmax - intent.z
                    intent.z += np.random.uniform(zspan, zspan + 1)

            case "d":  # deep shot
                # Adjust position depending on theoretical position
                xspan = intent.x - xmin
                intent.x -= np.random.uniform(xspan, xspan + 2)

            case "x" | "e":  # deep and wide or unknown error
                # Adjust position depending on theoretical position
                xspan = intent.x - xmin
                intent.x -= np.random.uniform(xspan, xspan + 2)
                if intent.z < court_zmid:
                    zspan = intent.z - zmin
                    intent.z -= np.random.uniform(zspan, zspan + 1)
                else:
                    zspan = zmax - intent.z
                    intent.z += np.random.uniform(zspan, zspan + 1)

    def trajectory(self):
        """
        Getter method for the full trajectory
        """
        return self.engine.traj
