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
    return court, single_court, serve_box


class Point:
    def __init__(self, point_data):
        self.court, self.single_court, self.serve_box = coordinates()

    def shot(self):
        pass

    def bounce(self):
        pass

    def point(self):
        pass


# The x-acceleraion is to simulate drag:
# in theory it should be proportional to the velocity,
# in practice the velocity difference between start and finish is
# relatively small and a constant acceleration is a good approximation.
a = vector(-1.5, -9.81, 0)
f = 60
dt = 1 / f


def initial_velocity(s_i, s_f, t):
    return (s_f - s_i) / (k * t) - a * t / 2


court_xz, single_court, serve_box = coordinates()

t = 0
# s0 must be defined this way to have a copy
# with s0 = court.ball.pos, s0 references the same object of ball.pos
s0 = vector(court.ball.pos.x, court.ball.pos.y, court.ball.pos.z)
v0 = initial_velocity(
    court.ball.pos, vector(-single_court.x, 0, -single_court.z), 0.75
)  # forehand: (30.5, 36)m/s range. backhand: (27.5, 33.5)m/s range. Angle (0,10) maybe

court.wait()
while court.ball.pos.y > 0:
    rate(f)
    t += dt
    court.ball.pos = s0 + k * (v0 * t + 0.5 * a * t**2)

court.wait()
