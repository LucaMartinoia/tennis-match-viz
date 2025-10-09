from court import TennisCourt
from dynamics import Point
from vpython import canvas, box, color, vector, sphere, distant_light, rate

court = TennisCourt()
court.create()

f = 30
dt = 1 / f
t = 0
g = vector(0, 9.81, 0)
v = vector(-18, 5, 0)

court.wait()
while court.ball.pos.y > 0:
    rate(f)
    court.ball.pos += v * dt - g * t * dt
    t += dt

court.wait()
