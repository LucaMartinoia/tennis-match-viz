import numpy as np
import random
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
    net = SimpleNamespace()
    net.center = 0.915
    net.sides = 1.07
    return court, single_court, serve_box, net


court, single_court, serve_box, net = coordinates()

# Seed for reproducibility
# random.seed(42)
# np.random.seed(42)

# Constants
G = 9.85  # m/s^2
A = 1  # m/s^2  # TO DO: scale with velocity and find realistic drag value (eventually per shot type)
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
                    yf = 0.0
                case "d":
                    xf, zf = self._random_point_in_bbox(SERVE_ERRORS.deep)
                    T = np.random.uniform(0.3, 0.45)
                    yf = 0.0
                case "x":
                    xf, zf = self._random_point_in_bbox(SERVE_ERRORS.widedeep)
                    T = np.random.uniform(0.3, 0.45)
                    yf = 0.0
        # Valid serve
        else:
            T = np.random.uniform(0.3, 0.45)
            yf = 0.0
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

        traj1 = self._serve_lob()
        s0 = traj1[-1]  # shape (3,)
        sf = np.array([xf, yf, zf], dtype=float)
        traj2 = self._trajectory(s0, sf, T)
        traj = np.vstack((traj1, traj2[1:]))

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
        traj = self._trajectory(s0, sf, T)
        return traj

    ############################################
    #       GLOBAL
    ############################################

    def shot_trajectory(self, shot):
        """
        This function takes the single shots and create the trajectory.

        [5b, b+38s, s1w, w#] or [6b, b28f, f3b, b3b, b2f, f3b, b3d, d@]
        """
        if len(shot) == 3:  # [a][0][a]
            pass
        if len(shot) == 4:  # [a][0][0][a] or [a][0][#][a]
            pass

    def _trajectory(self, s0, sf, T):
        """
        This is the most basic function, which computes the trajectory
        given the initial and final positions (as numpy arrays) and the time T.

        s0: numpy.array
        sf: numpy.array
        T: float

        return traj: numpy.array
        """
        # Compute the 2D angle
        theta = self._angle_xz(s0, sf)
        # Compute acceleration vector a
        if s0[0] == sf[0] and s0[2] == sf[2]:
            a = -np.array([0, G, 0])
        else:
            a = -np.array([A * np.cos(theta), G, A * np.sin(theta)])
        # Compute initial velocity v0
        v0 = (sf - s0 - 0.5 * a * T**2) / T
        # Compute the trajectory
        t = self._time_array(T)
        traj = s0 + v0[None, :] * t[:, None] + 0.5 * a[None, :] * t[:, None] ** 2

        return traj

    def _time_array(self, T):
        """
        This basic function returns a time array.
        """
        dt = 1 / FPS
        return np.arange(0, T + dt, dt)

    def _angle_xz(self, vec0, vecf):
        """
        Computes the 2D angle on the x-z plane between two vectors.
        """
        # Project onto x-z plane
        u = np.array([vec0[0], vec0[2]])
        v = np.array([vecf[0], vecf[2]])
        # Compute angle
        cross = u[0] * v[1] - u[1] * v[0]
        dot = np.dot(u, v)
        # Signed angle
        theta = np.arctan2(cross, dot)  # radians
        return theta

    def _velocity_heristic(self, x0, xf, T):
        """
        Returns an initial velocity estimate, assuming the decellaration is small.

        Used to scale the drag with velocity.
        """
        return np.linalg.norm(xf - x0) / T

    def _quadrant_selection(self):
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
