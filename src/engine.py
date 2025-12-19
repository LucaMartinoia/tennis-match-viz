import numpy as np
from types import SimpleNamespace

"""
This module is called in main and manages the core logic: it takes as input the single
rows of the database that is the output of parser.py and, for each tennis point, computes the
full trajectory of the ball.
"""


def coordinates():
    """
    Returns the x-z coordinates of various tennis court regions
    with respect to the origin at the center.
    """
    # Totale length and width (doubles)
    court = SimpleNamespace(x=23.77 / 2, z=10.97 / 2)
    # Totale length and width (single)
    single_court = SimpleNamespace(x=23.77 / 2, z=8.23 / 2)
    # Serve box length and width
    serve_box = SimpleNamespace(x=6.40, z=8.23 / 2)
    # Net height
    net = SimpleNamespace(center=0.915, sides=1.07)
    return court, single_court, serve_box, net


court, single_court, serve_box, net = coordinates()

# Seed for reproducibility
# random.seed(42)
# np.random.seed(42)

# Constants
G = 9.81  # m/s^2
V_FRACTION = 0.7
FRICTION = 0.85
ENERGY_BOUNCE = 0.5  # TO DO: scale with court type
FPS = 120
SERVE_ERRORS_STR = ["n", "w", "d", "x", "g"]
SERVE_AREAS = SimpleNamespace(
    wide=[-serve_box.x, -serve_box.z, -serve_box.x + 2, -serve_box.z * 3 / 4],
    downT=[-serve_box.x, -serve_box.z * 1 / 3, -serve_box.x + 2, 0],
    body=[-serve_box.x, -serve_box.z * 3 / 4, -serve_box.x + 2, -serve_box.z * 1 / 3],
    all=[-serve_box.x, -serve_box.z, -serve_box.x + 3, 0],
)
SERVE_ERRORS = SimpleNamespace(
    net=[0.06, -serve_box.z, 0.06, 0],
    wide=[-serve_box.x, -serve_box.z - 1, -serve_box.x + 2, -serve_box.z - 0.1],
    deep=[-serve_box.x - 1, -serve_box.z, -serve_box.x - 0.1, 0],
    widedeep=[
        -serve_box.x - 1,
        -serve_box.z - 1,
        -serve_box.x - 0.1,
        -serve_box.z - 0.1,
    ],
)


class Dynamics:
    def __init__(self, df):
        # Load the match dataframe
        self.match_df = df
        self.point_in_game = 0  # To compute the quadrant of the server

    ############################################
    #       SERVE
    ############################################

    def serve(self, serve_str):
        # Serve error
        if serve_str[-1] in SERVE_ERRORS_STR:
            match serve_str[-1]:
                case "n" | "g":
                    xf, zf = self._random_point_in_bbox(SERVE_ERRORS.net)
                    T = np.random.uniform(0.2, 0.35)
                    yf = np.random.uniform(0.3, 0.95)
                case "w":
                    xf, zf = self._random_point_in_bbox(SERVE_ERRORS.wide)
                    T = np.random.uniform(0.3, 0.45)
                    yf = 0.1
                case "d":
                    xf, zf = self._random_point_in_bbox(SERVE_ERRORS.deep)
                    T = np.random.uniform(0.3, 0.45)
                    yf = 0.1
                case "x":
                    xf, zf = self._random_point_in_bbox(SERVE_ERRORS.widedeep)
                    T = np.random.uniform(0.3, 0.45)
                    yf = 0.1
        # Valid serve
        else:
            T = np.random.uniform(0.3, 0.4)
            yf = 0.1
            match serve_str[0]:
                case "4":
                    xf, zf = self._random_point_in_bbox(SERVE_AREAS.wide)
                case "5":
                    xf, zf = self._random_point_in_bbox(SERVE_AREAS.body)
                case "6":
                    xf, zf = self._random_point_in_bbox(SERVE_AREAS.downT)
                case _:
                    xf, zf = self._random_point_in_bbox(SERVE_AREAS.all)
                    print(f"Unkown serve code value {serve_str[0]}.")

        throw = self._serve_lob()
        s0 = throw[-1]  # shape (3,)
        s1 = np.array([xf, yf, zf], dtype=float)
        serve, v_f = self._shot_trajectory(s0, s1, T)

        # Bounce
        if "*" in serve_str:
            h = 0.1
            bounce1, v_f = self._bounce(serve[-1], h, v_f)
            bounce2, _ = self._bounce(bounce1[-1], h, v_f)
            bounce = np.vstack((bounce1, bounce2))
        else:
            h = np.random.uniform(0.4, 1.4)
            bounce, _ = self._bounce(serve[-1], h, v_f)
        traj = np.vstack((throw, serve[1:], bounce[1:]))

        return traj

    def _serve_lob(self, h0=1.0):
        """
        Compute a vertical serve trajectory from 1 m to a random height between 2.5 and 3 m.
        Returns a NumPy array of shape (N, 3), one row per time step.
        """
        serve_h = np.random.uniform(2.5, 3.0)  # serve height
        T = np.random.uniform(0.5, 0.8)

        # From the end line
        s0 = np.array([single_court.x, h0, 0.2])
        sf = np.array([single_court.x, serve_h, 0.2])
        traj, _ = self._shot_trajectory(s0, sf, T)
        return traj

    ############################################
    #       SHOT
    ############################################

    def point_trajectory(self):
        pass

    def shot_trajectory(self, shot):
        """
        This function takes the single shots and create the trajectory.

        [5b, b+38s, s1w, w#] or [6b, b28f, f3b, b3b, b2f, f3b, b3d, d@]
        """
        if len(shot) == 3:  # [a][0][a]
            pass
        if len(shot) == 4:  # [a][0][0][a] or [a][0][#][a]
            pass

    ############################################
    #       GLOBAL
    ############################################

    def _parabolic_motion(self, s0, v0, a, T):
        # Compute the trajectory
        t = self._time_array(T)
        traj = s0 + v0[None, :] * t[:, None] + 0.5 * a[None, :] * t[:, None] ** 2
        # Final velocity
        v_f = v0 + a * T

        return traj, v_f

    def _shot_trajectory(self, s0, sf, T):
        """
        This is the most basic function, which computes the trajectory
        given the initial and final positions (as numpy arrays) and the time T.

        s0: numpy.array
        sf: numpy.array
        T: float

        return traj: numpy.array
        """
        # Combine into full 3D acceleration
        a = self._acceleration_vector(s0, sf, T)
        # Compute initial velocity v0
        v0 = (sf - s0 - 0.5 * a * T**2) / T

        return self._parabolic_motion(s0, v0, a, T)

    def _bounce(self, s0, h, vi):
        v_after = np.array([FRICTION * vi[0], -ENERGY_BOUNCE * vi[1], FRICTION * vi[2]])
        # Compute bounce time
        discriminant = v_after[1] ** 2 - 2 * G * h
        if discriminant < 0:
            raise ValueError(
                "No real solution: the ball cannot reach yf from y0 with given v0."
            )
        T = (v_after[1] + np.sqrt(discriminant)) / G
        a = self._acceleration_bounce(v_after, T)

        return self._parabolic_motion(s0, v_after, a, T)

    def _acceleration_vector(self, s0, sf, T):
        """
        Estimates the acceleration vector necessary to produce the
        desired (fractional) decrease in velocity.
        """
        # Horizontal displacement vector (XZ plane)
        delta_xz = np.array([sf[0] - s0[0], sf[2] - s0[2]])
        dist_xz = np.linalg.norm(delta_xz)
        if dist_xz == 0:
            a_xz = np.array([0, 0])  # purely vertical motion
        else:
            unit_xz = delta_xz / dist_xz
            # Contant horizontal acceleration magnitude
            a_mag = V_FRACTION * dist_xz / ((1 - V_FRACTION / 2) * T**2)
            # Horizontal acceleration vector
            a_xz = -a_mag * unit_xz
        # Vertical acceleration
        a_y = -G

        return np.array([a_xz[0], a_y, a_xz[1]])

    def _acceleration_bounce(self, v0, T):
        # Horizontal velocity vector
        v_xz = np.array([v0[0], v0[2]])
        speed_xz = np.linalg.norm(v_xz)
        # Approximate horizontal displacement
        dist_xz = speed_xz * T
        # Compute constant horizontal acceleration magnitude
        v_fraction = 0.5
        a_mag = v_fraction * dist_xz / ((1 - v_fraction / 2) * T**2)
        # Acceleration antiparallel to horizontal velocity
        a_xz = -a_mag * v_xz / speed_xz
        # Vertical acceleration
        a_y = -G
        # Combine into 3D vector
        return np.array([a_xz[0], a_y, a_xz[1]])

    def _time_array(self, T):
        """
        This basic function returns a time array.
        """
        dt = 1 / FPS
        return np.arange(0, T + dt, dt)

    def _quadrant_selection(self, point, server):
        """
        This function takes the score and the server (p1 or p2)
        and computes the final trajectory.

        This is done via symmetry: if p2 is serving, the trajectory is symmetrized
        along the x axis. If the score is "odd", then the trajectory is symmetrized
        along the z axis.
        """
        pass

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
