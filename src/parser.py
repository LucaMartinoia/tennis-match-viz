import numpy as np
from src.engine import coordinates
from dataclasses import dataclass
import re

"""
This module bridges Match and Engine: it takes the point data
and converts it to geometric quantities that can be passed to Engine.

TO DO:
- Implement higher diversity in shots (spin, fore-/back-hand)
"""


def net_f(z: float) -> float:
    """
    Function for the net chord.
    """
    return 0.004098 * z**2 + net.center


#######################
# Constants
#######################
court, single_court, serve_box, net = coordinates()
YGROUND = 0.15
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
    "1d": [0.4 * single_court.z, single_court.z],  # Left 30%
    "2d": [-0.4 * single_court.z, 0.4 * single_court.z],  # Middle 40%
    "3d": [-single_court.z, -0.4 * single_court.z],  # Right 30%
    "0dz": [-single_court.z, single_court.z],  # Unknown width
    # Short shots
    "1s": [  # Left 30%
        0.4 * single_court.z,
        single_court.z - 1.5,
    ],
    "2s": [-0.4 * single_court.z, 0.4 * single_court.z],  # Middle 40%
    "3s": [  # Right 30%
        -single_court.z + 1.5,
        -0.4 * single_court.z,
    ],
    "0sz": [
        -single_court.z + 1.5,
        single_court.z - 1.5,
    ],  # Unknown width
    # Depth
    "6": [-serve_box.x - 2, -0.5],  # Drop shots
    "7": [-serve_box.x, -2],  # Inside serve box
    "8": [-(serve_box.x + single_court.x) / 2, -serve_box.x],  # Close to serve box
    "9": [-single_court.x, -(serve_box.x + single_court.x) / 2],  # Close to baseline
    "0x": [-single_court.x, -1.5],  # Unknown depth
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
    The Parser class parses shot data into geometric quantities.
    """

    def __init__(self, engine):
        """
        Loads the physic engine.
        """
        self.engine = engine

    def run_point(self, point_data) -> bool:
        """
        Entry point to compute the trajectory.

        Extract the point data and call the rallies.
        """
        # Extract point data
        righthanded = (point_data.righthand1, point_data.righthand2)
        point_in_game = point_data.point
        server = point_data.server
        # First serve attempt
        if point_data.first[0]:
            self.engine.pause(1.0)
            result = self._run_rally(point_data.first, point_in_game)

            # Check if first serve was a fault
            if point_data.second[0]:
                self.engine.pause(1.0)
                result = self._run_rally(point_data.second, point_in_game)
        else:
            # If both serves are missing
            return False

        # Mirror depending on server side
        self._side_selection(server)
        # Return result
        return result

    def _run_rally(self, rally, point_in_game: int) -> bool:
        """
        Parse the rally list to compute the trajectory.
        """
        # Check for non-mapped or penalty points
        if rally in ("S", "R", "P", "Q"):
            return False

        # Call serve first
        if rally[0][0].isdigit():
            right = True if point_in_game % 2 == 0 else False
            self._serve(rally[0], right)
            # Then call the shots
            for i, shot in enumerate(rally[1:]):
                self._shot(shot, i + 1)
            # Return positive result
            return True
        else:
            return False  # Does not start with a serve

    def _serve(self, serve_str: str, right: bool = True) -> None:
        """
        Parse the serve string and compute the trajectory.
        """
        # Compute bbox
        serve_area = SERVE_BBOX.get(serve_str[0], SERVE_BBOX["all"])

        # Find landing spot
        xf, zf = self._random_point_in_bbox(serve_area)
        shot_data = ShotIntent(
            x=xf,
            y=YGROUND,
            z=zf,
            T=np.random.uniform(0.3, 0.4),
        )

        # If error, modify the landing spot
        if serve_str[-1] in ERRORS_STR:
            self._apply_error(shot_data, serve_str[-1], MODE_BBOX["serve"])

        # Adjust z coordinate depending on side of serve
        shot_data.z = -shot_data.z if right else shot_data.z

        # Serve shot
        v_f = self.engine.serve(
            shot_data.x, shot_data.y, shot_data.z, shot_data.T, right
        )

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

    def _shot(self, shot_str: str, shot_index: int) -> bool:
        """
        Parse the shot string and compute the trajectory.
        """
        # Finds side of court
        server = True if shot_index % 2 == 0 else False

        # Parse shot code: letter+(symbol)+(0-2 digits)+rest
        m = re.match(r"^([A-Za-z])([;^]?)(\d{0,2})(.*)$", shot_str)  # Regex match
        if not m:
            # If error, return False
            return False

        # Find shot type, landing position and response shot
        shot_type, extra, position, response = m.groups()

        # Default shot data
        shot_data = self._compute_landing_data(shot_type, extra, position, response)

        # Apply error
        response_char = response[0] if response and response[0].isalpha() else ""
        if any(c in response for c in "#@") or response_char in ERRORS_STR:
            error = response_char if response_char in ERRORS_STR else "e"
            self._apply_error(shot_data, error, MODE_BBOX["single"])

        # Count bounces
        if shot_data.net:
            n = 3
        elif any(c in shot_str for c in "*#@C") or response_char in ERRORS_STR:
            n = 2
        else:
            n = 1

        # Adjust x and z coordinates depending on side of court
        shot_data.z = shot_data.z if server else -shot_data.z
        shot_data.x = shot_data.x if server else -shot_data.x

        # Shot trajectory
        if ";" in extra:
            # Shot hit net cords
            v_f = self.engine.net_cord(
                shot_data.x, shot_data.y, shot_data.z, shot_data.T
            )
        else:
            # Normal shot
            v_f = self.engine.shot(shot_data.x, shot_data.y, shot_data.z, shot_data.T)

        # If net, fall down to ground
        if shot_data.net:
            v_f = self.engine.net_drop()

        # Append bounces if land on ground or net
        if shot_data.y == YGROUND or shot_data.net:
            self.engine.bounces(v_f, n)

        return True

    def _compute_landing_data(
        self, shot_type: str, extra: str, position: str, response: str
    ) -> ShotIntent:
        """
        Method to compute the landing data given
        the shot type, the position and the response shot.
        """
        # Read width and depth data
        width = position[0] if len(position) > 0 else ""
        depth = position[1] if len(position) > 1 else ""
        width += "d"
        # Compute default x and z bounds
        x_bounds = SINGLE_BBOX.get(depth, SINGLE_BBOX["0x"])
        z_bounds = SINGLE_BBOX.get(width, SINGLE_BBOX["0dz"])
        yf = YGROUND

        # Determine time T based on shot type
        match shot_type:
            # TO DO: differentiate between shots
            case "f" | "b" | "r" | "s" | "t" | "q":
                T = np.random.uniform(0.95, 1.25)  # Baseline shots
            case "v" | "z" | "h" | "i" | "j" | "k":
                T = np.random.uniform(0.6, 0.75)  # Voleè
            case "o" | "p":
                T = np.random.uniform(0.45, 0.55)  # Smash
            case "u" | "y":
                T = np.random.uniform(1.1, 1.65)  # Drop shot
            case "l" | "m":
                T = np.random.uniform(1.5, 2.5)  # Lob
            case _:
                T = np.random.uniform(0.95, 1.45)  # Unknown

        # Adjust landing depending on response shot
        # If response position is indicated
        if len(response) > 1 and response[1] in ("-", "="):
            match response[1]:
                # Response near net
                case "-":
                    T -= 0.1  # Reduce time
                    # If depth missing
                    depth = depth if depth else "7"  # Inside serve box
                    x_bounds = SINGLE_BBOX.get(depth)
                # Response near baseline
                case "=":
                    T += 0.1  # Increment time
                    # If depth missing
                    depth = depth if depth else "9"  # Near baseline
                    x_bounds = SINGLE_BBOX.get(depth)
        # If response position is not indicated
        else:
            # Check response type
            match response[0]:
                case "v" | "z" | "h" | "i" | "j" | "k":  # Voleè
                    T -= 0.1  # Reduce time
                    yf = np.random.uniform(0.8, 1.8)  # Hit mid air
                    # If depth missing
                    depth = depth if depth else "7"  # Inside serve box
                    width = width[0] + "s"
                    z_bounds = SINGLE_BBOX.get(width, SINGLE_BBOX["0sz"])  # Short width
                    x_bounds = SINGLE_BBOX.get(depth)

                case "o" | "p":  # Smash
                    yf = np.random.uniform(2.5, 3.5)  # Hit mid air
                    # If depth missing
                    depth = depth if depth else "8"  # From mid court
                    width = width[0] + "s"
                    z_bounds = SINGLE_BBOX.get(width, SINGLE_BBOX["0sz"])  # Short width
                    x_bounds = SINGLE_BBOX.get(depth)

                case "*":  # Winners
                    T -= 0.1  # Faster shot
                    yf = YGROUND
                    x_bounds = SINGLE_BBOX.get("9")

        # Check for volè drop shot
        if extra == "^":
            x_bounds = SINGLE_BBOX.get("6")
            yf = YGROUND
            T += 0.2

        xf, zf = self._random_point_in_bbox(
            [x_bounds[0], z_bounds[0], x_bounds[1], z_bounds[1]]
        )

        return ShotIntent(
            x=xf,
            y=yf,
            z=zf,
            T=T,
        )

    def _side_selection(self, server: int = 1):
        """
        This function takes the server side (1 or 2)
        and computes the final trajectory.

        If p2 is serving, the trajectory is symmetrized along the x and z axis.
        """
        lambdax = 1 if server == 1 else -1
        lambdaz = 1 if server == 1 else -1

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
                intent.T = np.random.uniform(0.4, 0.55)
                intent.y = np.random.uniform(0.5, 0.91)
                intent.net = True

            case "w":  # Wide shot
                # Adjust position depending on theoretical position
                if intent.z < court_zmid:
                    zspan = intent.z - zmin + 0.1
                    intent.z -= np.random.uniform(zspan, zspan + 1)
                else:
                    zspan = zmax - intent.z + 0.1
                    intent.z += np.random.uniform(zspan, zspan + 1)

            case "d":  # deep shot
                # Adjust position depending on theoretical position
                xspan = intent.x - xmin + 0.1
                intent.x -= np.random.uniform(xspan, xspan + 2)

            case "x" | "e":  # deep and wide or unknown error
                # Adjust position depending on theoretical position
                xspan = intent.x - xmin + 0.1
                intent.x -= np.random.uniform(xspan, xspan + 2)
                if intent.z < court_zmid:
                    zspan = intent.z - zmin + 0.1
                    intent.z -= np.random.uniform(zspan, zspan + 1)
                else:
                    zspan = zmax - intent.z + 0.1
                    intent.z += np.random.uniform(zspan, zspan + 1)
