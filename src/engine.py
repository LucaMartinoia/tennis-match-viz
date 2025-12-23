import numpy as np
from types import SimpleNamespace

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
G = 9.81  # m/s^2


class Engine:
    """
    The physic engine that computes the ball trajectories.
    """

    def __init__(self, court="hard"):
        """
        Keep track of trajectory and physic quantities.
        """
        # Load the match dataframe
        self.traj = np.empty((0, 3))  # One point per timestep
        self.court = court
        self.v_fraction = 0.7  # TO DO: scale with court type
        self.friction = 0.85  # TO DO: scale with court type
        self.energy_loss_bounce = 0.65  # TO DO: scale with court type
        self.fps = 60

    def serve(self, xf: float, yf: float, zf: float, T: float):
        """
        Takes the landing spot and compute the serve trajectory.

        Return the final velocity.
        """
        self._serve_lob()
        s0 = self._last_point()  # shape (3,)
        s1 = np.array([xf, yf, zf], dtype=float)
        return self._shot_trajectory(s0, s1, T)

    def _serve_lob(self, h0: float = 1.0) -> None:
        """
        Compute the vertical hand throw.
        """
        # Throw parameters
        serve_h = np.random.uniform(2.7, 3.4)
        T = np.random.uniform(0.5, 0.8)

        # From the end line
        s0 = np.array([single_court.x, h0, 0.2])
        sf = np.array([single_court.x, serve_h, 0.2])

        self._shot_trajectory(s0, sf, T)

    def shot(self, xf: float, yf: float, zf: float, T: float, side: str):
        """
        Takes the landing spot and compute the shot trajectory.

        Return the final velocity.
        """
        s0 = self._last_point()  # shape (3,)
        s1 = np.array([xf, yf, zf], dtype=float)
        # Check court side
        if side == "defender":
            s1[0] = -s1[0]
            s1[2] = -s1[2]

        return self._shot_trajectory(s0, s1, T)

    def _shot_trajectory(self, s0, sf, T: float):
        """
        This is the basic function which computes the trajectory
        given the initial and final positions and the time.
        """
        # Compute 3D acceleration
        a = self._acceleration_vector(s0, sf, T)
        # Compute initial velocity v0
        v0 = (sf - s0 - 0.5 * a * T**2) / T
        # Update trajectory and return final velocity
        return self._parabolic_motion(s0, v0, a, T)

    def _parabolic_motion(self, s0, v0, a, T: float):
        """
        Take the initial data, acceleration and time to compute the parabolic motion.

        Return final velocity.
        """
        # Compute the trajectory
        t = self._time_array(T)
        traj = s0 + v0[None, :] * t[:, None] + 0.5 * a[None, :] * t[:, None] ** 2
        self.traj = np.vstack((self.traj, traj))

        # Final velocity
        v_f = v0 + a * T
        return v_f

    def _bounce(self, s0, h: float, vi):
        """
        Compute a single bounce given the initial position, velocity and final height.
        """
        # Compute bounce time
        discriminant = vi[1] ** 2 - 2 * G * h
        if discriminant < 0:
            raise ValueError(
                "No real solution: the ball cannot reach yf from y0 with given v0."
            )
        T = (vi[1] + np.sqrt(discriminant)) / G
        # Compute 3D acceleration using initial velocity instead of s0 and sf.
        a = self._acceleration_bounce(vi, T)

        return self._parabolic_motion(s0, vi, a, T)

    def bounces(self, vi, n: int) -> None:
        """
        Compute multiple bounces and concatenate them,
        """
        s0 = self._last_point()
        # Compute the velocity right after the bounce
        v_after = np.array(
            [
                self.friction * vi[0],
                -self.energy_loss_bounce * vi[1],
                self.friction * vi[2],
            ]
        )
        # If single bounce, the ball is returned
        if n == 1:
            hmax = v_after[1] ** 2 / (2 * G)
            h = (
                np.random.uniform(hmax / 2, hmax)
                if hmax < 1.7
                else np.random.uniform(0.5, 1.7)
            )
            self._bounce(s0, h, v_after)
        # Otherwise bounce to ground
        else:
            for _ in range(n):
                h = 0.0
                vi = self._bounce(s0, h, v_after)
                v_after = np.array(
                    [
                        self.friction * vi[0],
                        -self.energy_loss_bounce * vi[1],
                        self.friction * vi[2],
                    ]
                )
                s0 = self._last_point()

    def _acceleration_vector(self, s0, sf, T: float):
        """
        Estimate the acceleration vector necessary to produce the
        desired (fractional) decrease in velocity.
        """
        # Horizontal displacement vector (XZ plane)
        delta_xz = np.array([sf[0] - s0[0], sf[2] - s0[2]])
        dist_xz = np.linalg.norm(delta_xz)
        if dist_xz == 0:  # purely vertical motion
            a_xz = np.array([0, 0])
        else:
            unit_xz = delta_xz / dist_xz
            # Contant horizontal acceleration magnitude
            a_mag = self.v_fraction * dist_xz / ((1 - self.v_fraction / 2) * T**2)
            # Horizontal acceleration vector
            a_xz = -a_mag * unit_xz
        # Vertical acceleration
        a_y = -G

        return np.array([a_xz[0], a_y, a_xz[1]])

    def _acceleration_bounce(self, v0, T: float):
        """
        Compute the acceleration given the initial velocity.
        """
        # Horizontal velocity vector
        v_xz = np.array([v0[0], v0[2]])
        speed_xz = np.linalg.norm(v_xz)
        if speed_xz:
            # Approximate horizontal displacement
            dist_xz = speed_xz * T
            v_fraction = 0.5
            # Compute constant horizontal acceleration magnitude
            a_mag = v_fraction * dist_xz / ((1 - v_fraction / 2) * T**2)
            # Acceleration antiparallel to horizontal velocity
            a_xz = -a_mag * v_xz / speed_xz
        else:  # If vertical motion
            a_xz = [0, 0]
        # Vertical acceleration
        a_y = -G

        # Return 3D vector
        return np.array([a_xz[0], a_y, a_xz[1]])

    def _time_array(self, T: float):
        """
        Returns a time array.
        """
        dt = 1 / self.fps
        return np.arange(0, T + dt, dt)

    def pause(self, T: float):
        """
        Append empty vectors for T seconds.
        """
        t = self._time_array(T)
        pause_traj = np.full((len(t), 3), np.nan)
        self.traj = np.vstack((self.traj, pause_traj))

    def net_drop(self):
        """
        Free fall from stationary.
        """
        # Stationary at a given height
        s0 = self._last_point()
        v0 = np.array([0, 0, 0])
        a = np.array([0, -G, 0])
        T = np.sqrt(2 * s0[1] / G)
        return self._parabolic_motion(s0, v0, a, T)

    def net_cord(self, xf, yf, zf, T, side):
        """
        Shot that hits the net and lands in.
        Attache two consecutive parabolic trajectories.
        """
        s0 = self._last_point()
        # Landing point
        s2 = np.array([xf, yf, zf], dtype=float)
        # Check court side
        if side == "defender":
            s2[0] = -s2[0]
            s2[2] = -s2[2]
        # Find where the ball hits the net
        alpha = -s0[0] / (s2[0] - s0[0])
        z1 = s0[2] + alpha * (s2[2] - s0[2])
        s1 = np.array([0.0, 0.95, z1])
        # Compute the two trajectories
        T1 = T / 2
        T2 = np.random.uniform(T * 3 / 4, T)
        self._shot_trajectory(s0, s1, T1)
        return self._shot_trajectory(s1, s2, T2)  # Long time for lob effect

    def reset(self):
        """
        Reset the trajectory to null state.
        """
        self.traj = np.empty((0, 3))

    def set_FPS(self, fps: int) -> None:
        """
        Setter method for the FPS.
        """
        self.fps = fps

    def _last_point(self):
        """
        Getter method for the last point in trajectory.
        """
        return self.traj[-1]

    def apply_symmetry(self, lambdax: int = 1, lambdaz: int = 1):
        """
        Apply symmetry to the trajectory.
        lambdax, lambdaz: +1 or -1. -1 flips the respective axis.
        """
        if self.traj.size == 0:
            return  # nothing to flip

        self.traj[:, 0] *= lambdax  # flip x if -1
        self.traj[:, 2] *= lambdaz  # flip z if -1
