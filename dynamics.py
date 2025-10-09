from vpython import canvas, box, color, vector, sphere, distant_light
import numpy as np
from court import coordinates


class Point:
    def __init__(self):
        self.court, self.single_court, self.serve_box = coordinates()

    def shot(self):
        pass

    def parser(self):
        pass
