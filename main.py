from src.database import Database
from src.match import Match
from src.gui_vpython import GUI

"""
TO DO:
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


if __name__ == "__main__":

    bus = EventBus()

    gui = GUI(bus)
    database = Database(bus)
    match = Match(bus)

    # Main entry point
    database.load_tournament_list()
    # gui.set_default_tournament(t_name) # Read from config
