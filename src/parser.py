import numpy as np
from src.engine import coordinates
from dataclasses import dataclass
import re

"""
This module manages the core logic: it takes the match database and,
for each point, computes the full trajectory of the ball.
"""

np.random.seed(1)

#######################
# Constants
#######################
court, single_court, serve_box, net = coordinates()
ERRORS_STR = ["n", "w", "d", "x", "g", "e"]  # Error code
# Court bbox
MODE_BBOX = {
    "serve": [-serve_box.x, -serve_box.z, 0, 0],
    "single": [-single_court.x, -single_court.z, 0, single_court.z],
}
# Serve region bbox
SERVE_BBOX = {
    "4": [-serve_box.x, -serve_box.z, -serve_box.x + 2, -serve_box.z * 3 / 4],  # Wide
    "6": [-serve_box.x, -serve_box.z * 1 / 3, -serve_box.x + 2, 0],  # Down the T
    "5": [  # Body
        -serve_box.x,
        -serve_box.z * 3 / 4,
        -serve_box.x + 2,
        -serve_box.z * 1 / 3,
    ],
    "all": [-serve_box.x, -serve_box.z, -serve_box.x + 2, 0],
}
# Single region bbox
SINGLE_BBOX = {
    # Deep shots
    "1d": [-single_court.z, -0.4 * single_court.z],  # Left 30%
    "2d": [-0.4 * single_court.z, 0.4 * single_court.z],  # Middle 40%
    "3d": [0.4 * single_court.z, single_court.z],  # Right 40%
    "0dz": [-single_court.z, single_court.z],  # Unknown width
    # Short shots
    "1s": [
        -single_court.z + 1.5,
        -0.4 * single_court.z,
    ],  # Left 30%
    "2s": [-0.4 * single_court.z, 0.4 * single_court.z],  # Middle 40%
    "3s": [
        0.4 * single_court.z,
        single_court.z - 1.5,
    ],  # Right 30%
    "0sz": [
        -single_court.z + 1.5,
        single_court.z - 1.5,
    ],  # Unknown width
    # Depth
    "7": [-serve_box.x, -2],  # Inside serve box
    "8": [-(serve_box.x + single_court.x) / 2, -serve_box.x],  # Close to serve box
    "9": [-single_court.x, -(serve_box.x + single_court.x) / 2],  # Close to baseline
    "0x": [-single_court.x, -2],  # Unknown depth
}


@dataclass
class ShotIntent:
    x: float
    y: float
    z: float
    T: float
    net: bool = False


class Parser:
    """
    The match class parses shot data into geometric quantities.
    """

    def __init__(self, engine):
        """
        Loads the match data and keep track of points.
        """
        # Load the match dataframe
        self.engine = engine

    def _serve(self, serve_str: str) -> None:
        """
        Parse the serve string and compute the trajectory.
        """
        # Compute bbox
        serve_area = SERVE_BBOX.get(serve_str[0], SERVE_BBOX["all"])

        # Find landing spot
        xf, zf = self._random_point_in_bbox(serve_area)
        shot_data = ShotIntent(
            x=xf,
            y=0.05,
            z=zf,
            T=np.random.uniform(0.3, 0.4),
        )

        # If error, modify the landing spot
        if serve_str[-1] in ERRORS_STR:
            self._apply_error(shot_data, serve_str[-1], MODE_BBOX["serve"])

        # Serve shot
        v_f = self.engine.serve(shot_data.x, shot_data.y, shot_data.z, shot_data.T)

        # If net, fall down to ground
        if shot_data.net:
            v_f = self.engine.net_drop()

        # Bounces
        if shot_data.net:
            n = 3
        elif any(c in serve_str for c in "*#C") or serve_str[-1] in ERRORS_STR:
            n = 2
        else:
            n = 1

        self.engine.bounces(v_f, n)

    def run_point(self, point_data):
        """
        Extract the point data and call the serve and shot functions.
        """
        # Extract point data
        righthanded1 = point_data.hand1
        righthanded2 = point_data.hand2

        # First serve attempt
        if point_data.first:
            self._run_rally(point_data.first)

            # Check if first serve was a fault
            if point_data.second:
                self.engine.pause(1.0)
                self._run_rally(point_data.second)
            else:
                return "Failed to compute trajectory."

        self._quadrant_selection(point_data.server, point_data.point)

        return "Trajectory computed successfully."

    def _run_rally(self, rally):
        """
        Compute the rally trajectory.
        """
        # Check for non-mapped or penalty points
        if rally in ("S", "R", "P", "Q"):
            return

        # Call serve first, then the shots
        if rally[0][0].isdigit():
            self._serve(rally[0])

            for i, shot in enumerate(rally[1:]):
                self._shot(shot, i + 1)
        else:
            return  # Does not start with a serve

    def _shot(self, shot_str: str, i: int, righthanded: bool = True) -> None:
        """
        This function takes the single shots and create the trajectory.
        """
        # Finds side of court
        side = "server" if i % 2 == 0 else "defender"

        # Parse shot code
        m = re.match(r"^([A-Za-z])([;^]?)(\d{0,2})(.+)$", shot_str)  # Regex match
        if not m:
            raise ValueError(f"Invalid shot string: {shot_str}")

        # Find shot type, landing position and response shot
        shot_type, extra, position, response = m.groups()
        l = len(shot_str)

        # Default shot data
        shot_data = self._compute_landing_data(shot_type, extra, position, response)

        # Apply error
        response_char = response[0] if response and response[0].isalpha() else ""
        if any(c in response for c in "#@") or response_char in ERRORS_STR:
            error = response_char if response_char in ERRORS_STR else "e"
            self._apply_error(shot_data, error, MODE_BBOX["single"])

        # Bounces
        if shot_data.net:
            n = 3
        elif any(c in shot_str for c in "*#@C") or response_char in ERRORS_STR:
            n = 2
            if "*" in shot_str:  # If winner, shot is faster
                shot_data.T -= 0.2
        else:
            n = 1

        # Shot trajectory
        if ";" not in extra:
            v_f = self.engine.shot(
                shot_data.x, shot_data.y, shot_data.z, shot_data.T, side=side
            )
        else:
            # Net cord
            v_f = self.engine.net_cord(
                shot_data.x, shot_data.y, shot_data.z, shot_data.T, side=side
            )

        # If net, fall down to ground
        if shot_data.net:
            v_f = self.engine.net_drop()
        # Append bounces
        self.engine.bounces(v_f, n)

        print(
            f"-- Shot number {i}: {shot_str} --\n"
            + f"pattern: {shot_type}, {extra}, {position}, {response}; length {l}"
        )

        # Apply symmetries
        if righthanded:
            self.engine.apply_symmetry(lambdaz=-1)

    def _compute_landing_data(
        self, shot_type: str, extra: str, position: str, response: str
    ) -> ShotIntent:
        """
        Helpher method to compute the default landing data given
        the shot, the position and the response shot.
        """
        # Read width and depth data
        width = position[0] if len(position) > 0 else ""
        depth = position[1] if len(position) > 1 else ""
        width += "d"
        # Compute x and z bounds
        x_bounds = SINGLE_BBOX.get(depth, SINGLE_BBOX["0x"])
        z_bounds = SINGLE_BBOX.get(width, SINGLE_BBOX["0dz"])
        yf = 0.05

        # Determine time T based on shot type
        match shot_type:
            # TO DO: differentiate between shots
            case "f" | "b" | "r" | "s" | "t" | "q":
                T = np.random.uniform(1.05, 1.45)  # Baseline shots
            case "v" | "z" | "h" | "i" | "j" | "k":
                T = np.random.uniform(0.2, 0.35)  # Voleè
            case "o" | "p":
                T = np.random.uniform(0.2, 0.35)  # Smash
            case "u" | "y":
                T = np.random.uniform(0.6, 0.85)  # Drop shot
            case "l" | "m":
                T = np.random.uniform(1, 1.5)  # Lob
            case _:
                T = np.random.uniform(0.3, 0.45)  # Unknown

        # Adjust landing depending on response shot
        if len(response) > 1 and response[1] in ("-", "="):
            # If response position is indicated
            match response[1]:
                case "-":
                    T -= 0.1  # Reduce time
                    # If depth missing
                    depth = depth if depth else "7"  # Inside serve box
                    width += "s"
                    z_bounds = SINGLE_BBOX.get(width, SINGLE_BBOX["0dz"])  # Short width
                    x_bounds = SINGLE_BBOX.get(depth)
                case "=":
                    T += 0.1  # Increment time
                    # If depth missing
                    depth = depth if depth else "9"  # Inside serve box
                    width += "d"
                    z_bounds = SINGLE_BBOX.get(width, SINGLE_BBOX["0dz"])  # Short width
                    x_bounds = SINGLE_BBOX.get(depth)
        else:
            match response[0]:
                case "v" | "z" | "h" | "i" | "j" | "k":  # Voleè
                    T -= 0.1  # Reduce time
                    yf = (
                        0.05 if "^" in extra else np.random.uniform(0.8, 1.8)
                    )  # Bounce check
                    # If depth missing
                    depth = depth if depth else "7"  # Inside serve box
                    width += "s"
                    z_bounds = SINGLE_BBOX.get(width, SINGLE_BBOX["0sz"])  # Short width
                    x_bounds = SINGLE_BBOX.get(depth)

                case "o" | "p":  # Smash
                    yf = np.random.uniform(2.0, 2.5)  # Before bounce
                    # If depth missing
                    depth = depth if depth else "8"  # From mid court
                    width += "s"
                    z_bounds = SINGLE_BBOX.get(width, SINGLE_BBOX["0sz"])  # Short width
                    x_bounds = SINGLE_BBOX.get(depth)

        xf, zf = self._random_point_in_bbox(
            [x_bounds[0], z_bounds[0], x_bounds[1], z_bounds[1]]
        )

        return ShotIntent(
            x=xf,
            y=yf,
            z=zf,
            T=T,
        )

    def _quadrant_selection(self, server: int = 1, point_in_game: int = 0):
        """
        This function takes the score and the server (p1 or p2)
        and computes the final trajectory.

        This is done via symmetry: if p2 is serving, the trajectory is symmetrized
        along the x axis. If the score is "odd", then the trajectory is symmetrized
        along the z axis.
        """
        lambdax = 1
        lambdaz = -1

        if server == 2:
            lambdax = -1
            lambdaz = 1

        if point_in_game % 2 == 1:
            lambdaz = -lambdaz

        self.engine.apply_symmetry(lambdax=lambdax, lambdaz=lambdaz)

    def _random_point_in_bbox(self, bbox):
        """
        Computes uniformly random coordinate values for a given bounding box.
        """
        x1, z1, x2, z2 = bbox
        xmin, xmax = sorted((x1, x2))
        zmin, zmax = sorted((z1, z2))
        x = np.random.uniform(xmin, xmax)
        z = np.random.uniform(zmin, zmax)
        return x, z

    def _apply_error(self, intent: ShotIntent, err: str, mode_bbox) -> None:
        """
        Apply error effects to a shot.
        """
        # Court parameters
        xmin, zmin, _, zmax = mode_bbox
        court_zmid = 0.5 * (mode_bbox[1] + mode_bbox[3])

        match err:
            case "n" | "g":  # Net or foot fault
                # Recompute all values
                intent.x = 0.2
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
