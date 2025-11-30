from court import TennisCourt, coordinates
from dynamics import Point
from vpython import vector, rate, mag

k = 1  # TO DO: slowmotion parameter

# The x-acceleraion is to simulate drag:
# in theory it should be proportional to the velocity,
# in practice the velocity difference between start and finish is
# relatively small and a constant acceleration is a good approximation.
a = vector(-1.5, -9.81, 0)
f = 60
dt = 1 / f

court = TennisCourt()
court.create()


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
