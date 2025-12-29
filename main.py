from src.database import Database
from src.match import Match
from src.gui_vpython import GUI

"""
TO DO:
- Write def main()
- Check everything
- Document every functions
- Write README
- Create installer with .exe file
"""


class EventBus:
    def __init__(self):
        self._subs = {}
        self._topics = set()

    def subscribe(self, event, fn):
        self._topics.add(event)
        self._subs.setdefault(event, []).append(fn)

    def emit(self, event, **payload):
        self._topics.add(event)
        for fn in self._subs.get(event, []):
            fn(**payload)

    @property
    def topics(self):
        return list(self._topics)


# Callback for when a tournament is selected in the GUI
def on_match_selected(match_name):
    # Get the match dataframe from Database
    database.set_match(match_name)
    match_df = database.get_match_data()
    # Pass it to Match
    match.select_df(match_df)
    # Emit an event that GUI can listen to
    bus.emit("match_metadata_updated", metadata=database.get_match_metadata())
    bus.emit("update-score", score=match.update_score_data())
    match.select_point(1)


if __name__ == "__main__":

    bus = EventBus()

    gui = GUI(bus)
    database = Database(bus)
    match = Match(bus)

    # Subscribe to the event
    bus.subscribe("tournament_selected", database.on_tournament_selected)
    bus.subscribe("match_selected", on_match_selected)

    tournament_list = database.tournaments_list()
    gui.set_tournament_menu(tournament_list)
    # gui.set_default_tournament(t_name) # Read from config

    # gui.wait()
