from src.database import Database
from src.match import Match
from src.gui_vpython import TennisCourt

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
    database = Database()
    database.matches_list("US Open 2022")
    match_df = database.match_data("F - Ruud vs Alcaraz")

    # print(match_df.head(20))

    court = TennisCourt()
    court.create()

    match = Match(match_df)

    match.select_point(4)

    match.shot("b28f")
    match.serve("4w")
    court.animate_trajectory(match.trajectory())
