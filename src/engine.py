import numpy as np
from types import SimpleNamespace

"""
This module is the physic engine: it takes the initial and final position
and computes the full trajectory of the ball.

TO DO:
- Adjust parameters
- Spin effects
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
    The physic engine that computes the ball trajectory.
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
        self.fps = 100

    def serve(self, xf: float, yf: float, zf: float, T: float, right: bool):
        """
        Take the landing spot and side of serve and compute the serve trajectory.

        Return the final velocity.
        """
        # Hand throw
        self._serve_lob(right)
        # Initial position
        s0 = self._last_point()  # Shape (3,)
        # Final position
        s1 = np.array([xf, yf, zf], dtype=float)
        # Compute trajectory and return final velocity
        return self._shot_trajectory(s0, s1, T)

    def _serve_lob(self, right, h0: float = 1.0) -> None:
        """
        Compute the trajectory for the vertical hand throw.
        """
        # Throw parameters
        serve_h = np.random.uniform(2.7, 3.4)
        T = np.random.uniform(0.5, 0.8)
        z_shift = -0.2 if right else 0.2
        # From the end line
        s0 = np.array([single_court.x, h0, z_shift])
        sf = np.array([single_court.x, serve_h, z_shift])
        # Compute trajectory
        self._shot_trajectory(s0, sf, T)

    def shot(self, xf: float, yf: float, zf: float, T: float):
        """
        Takes the landing spot and compute the shot trajectory.

        Return the final velocity.
        """
        # Initial position
        s0 = self._last_point()  # Shape (3,)
        # Final position
        s1 = np.array([xf, yf, zf], dtype=float)
        # Compute trajectory and return final velocity
        return self._shot_trajectory(s0, s1, T)

    def _shot_trajectory(self, s0, sf, T: float):
        """
        This is the basic function which computes the trajectory
        given the initial and final positions and the time.

        Return the final velocity.
        """
        # Compute acceleration
        a = self._acceleration_vector(s0, sf, T)
        # Compute initial velocity v0
        v0 = (sf - s0 - 0.5 * a * T**2) / T
        # Compute trajectory and return final velocity
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

    def bounces(self, vi, n: int) -> None:
        """
        Compute multiple bounces and concatenate them.
        """
        # Initial position
        s0 = self._last_point()
        # Compute the velocity right after the bounce
        v_after = np.array(
            [
                self.friction * vi[0],
                -self.energy_loss_bounce * vi[1],
                self.friction * vi[2],
            ]
        )
        # If single bounce, stop at response h
        if n == 1:
            hmax = v_after[1] ** 2 / (2 * G)
            h = (
                np.random.uniform(hmax / 3, hmax)
                if hmax < 1.7
                else np.random.uniform(0.5, 1.7)
            )
            self._bounce(s0, h, v_after)
        # Otherwise bounce to ground n times
        else:
            for _ in range(n):
                h = 0.0  # Land on ground
                vi = self._bounce(s0, h, v_after)
                v_after = np.array(
                    [
                        self.friction * vi[0],
                        -self.energy_loss_bounce * vi[1],
                        self.friction * vi[2],
                    ]
                )
                s0 = self._last_point()

    def _bounce(self, s0, h: float, vi):
        """
        Compute a single bounce given the initial position, velocity and final height.

        Return final velocity.
        """
        # Compute bounce time
        discriminant = vi[1] ** 2 - 2 * G * h
        if discriminant < 0:
            # Clamp to reachable maximum height
            h = vi[1] ** 2 / (2 * G)
            discriminant = 0.0
            print(
                f"WARNING! Bounce: the ball cannot reach h={h:.1f} with given v0_y={vi[1]:.1f}."
            )
        # Compute solutions
        t1 = (vi[1] + np.sqrt(discriminant)) / G
        t2 = (vi[1] - np.sqrt(discriminant)) / G
        # Keep only positive solutions
        candidates = [t for t in (t1, t2) if t > 0]
        # Extract a time
        T = np.random.choice(candidates)
        # Compute acceleration using initial velocity
        a = self._acceleration_for_bounce(vi, T)
        # Compute trajectory and return final velocity
        return self._parabolic_motion(s0, vi, a, T)

    def net_drop(self):
        """
        Free fall from stationary.

        Return final velocity.
        """
        # Stationary at a given height
        s0 = self._last_point()
        v0 = np.array([0, 0, 0])
        a = np.array([0, -G, 0])
        T = np.sqrt(2 * s0[1] / G)
        # Compute trajectory and return final velocity
        return self._parabolic_motion(s0, v0, a, T)

    def net_cord(self, xf: float, yf: float, zf: float, T: float):
        """
        Shot that hits the net and lands in.
        Attache two consecutive parabolic trajectories.

        Return final velocity.
        """
        # Initial position
        s0 = self._last_point()
        # Landing position
        s2 = np.array([xf, yf, zf], dtype=float)
        # Find where the ball hits the net
        alpha = -s0[0] / (s2[0] - s0[0])
        z1 = s0[2] + alpha * (s2[2] - s0[2])
        # Adjust net position to avoid clipping
        s1x = 0.1 if s0[0] > 0 else -0.1
        s1 = np.array([s1x, 0.95, z1])
        # Compute the two trajectories
        T1 = T * 0.5
        T2 = np.random.uniform(T * 0.52, T)  # Long time for lob effect
        self._shot_trajectory(s0, s1, T1)
        s1 = self._last_point()
        # Compute trajectory and return final velocity
        return self._shot_trajectory(s1, s2, T2)

    def _acceleration_vector(self, s0, sf, T: float):
        """
        Estimate the acceleration vector necessary to produce the
        desired (fractional) decrease in velocity.

        Return 3D acceleration vector (np.array[x,y,z]).
        """
        # Horizontal displacement vector (XZ plane)
        delta_xz = np.array([sf[0] - s0[0], sf[2] - s0[2]])
        dist_xz = np.linalg.norm(delta_xz)
        # Purely vertical motion, no drag
        if dist_xz == 0:
            a_xz = np.array([0, 0])
        else:
            unit_xz = delta_xz / dist_xz
            # Contant horizontal acceleration magnitude
            a_mag = self.v_fraction * dist_xz / ((1 - self.v_fraction / 2) * T**2)
            # Horizontal acceleration vector
            a_xz = -a_mag * unit_xz
        # Vertical acceleration
        a_y = -G
        # Return acceleration vector
        return np.array([a_xz[0], a_y, a_xz[1]])

    def _acceleration_for_bounce(self, v0, T: float):
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
        # Return acceleration vector
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
            return  # Nothing to flip

        self.traj[:, 0] *= lambdax  # Flip x if -1
        self.traj[:, 2] *= lambdaz  # Flip z if -1
