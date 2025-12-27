from src.database import Database
from src.match import Match
from src.gui_vpython import GUI

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

    database = Database()
    database.matches_list("US Open 2022")
    match_df = database.match_data("F - Ruud vs Alcaraz")

    tournament_list = database.tournaments_list()

    gui = GUI()
    gui.bind_GUI(database.matches_list)
    gui.create(tournament_list)
    # gui.set_default_tournament(t_name) # Read from config

    gui.update_match_data("Ruud", "Alcaraz", "US Open 2022")
    for i in range(100):
        gui.GUI_print("test")
        gui.GUI_print("puzzo")

    match = Match()

    gui.court.animate_trajectory(match.trajectory)
    gui.wait()
