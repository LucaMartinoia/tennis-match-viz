from src.parser import Parser
from src.engine import coordinates, Dynamics
from src.gui_vpython import TennisCourt
import pandas as pd

"""
In main we should:
0. Setup the global GUI (buttons, canva, search, loops, etc...)
1. Call parser to read the file and parse the data
2. Call dynamics to transform the data in a series of points to be used in the animation
3. Call court to visualize the animation

One BIG advantage of the above stack (file -> parser -> dynamics -> visualization) is that if we later on want to
change the frontend GUI with something else (Panda3D or Qt) we only have to change court.py.
"""


if __name__ == "__main__":
    """
    1. Reads config file
    2. Inizialize parser (match list)
    3. Initialize GUI
    4. Select match
    5. Parse match
    6. Call dynamics on parsed data
    7. Call GUI on dynamics data
    8. Global loop
    """
    """
    renderer = None
    if renderer == "vpython":
        from src.gui_vpython import TennisCourt
    """
    parser = Parser()
    parser.matches_list("US Open 2022")
    match_df = parser.match_data("F - Ruud vs Alcaraz")

    court = TennisCourt()
    court.create()

    engine = Dynamics(match_df)

    pos = engine.serve("5*")
    court.animate_trajectory(pos)
