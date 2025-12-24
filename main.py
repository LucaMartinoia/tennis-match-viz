from src.database import Database
from src.match import Match
from src.gui_vpython import TennisCourt

"""
TO DO:
- Understand how to manage the main loop
- Write def main()
- Check everything
- Document every functions
- Write README
- Create installer with .exe file
"""


def main() -> None:
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
    pass


if __name__ == "__main__":

    # database = Database()
    # database.matches_list("US Open 2022")
    # match_df = database.match_data("F - Ruud vs Alcaraz")

    # print(match_df.head(20))

    court = TennisCourt()
    court.create()

    match = Match()

    # match.select_point(4)

    match.parser._serve("4f", right=False)
    match.parser._shot("f19f", 1)
    match.parser._shot("f1w#", 2)
    match.parser._side_selection(1)
    court.animate_trajectory(match.trajectory)
