from src.database import Database
from src.match import Match
from src.gui_vpython import GUI


def read_config():
    """
    Read the config.txt file.
    """
    fname = None
    t_name = None

    with open("config.txt", "r") as f:
        for line in f:
            # Remove comments
            line = line.split("#", 1)[0].strip()
            if not line:
                continue  # Skip empty lines
            if "=" not in line:
                continue  # Ignore malformed lines
            # Gather key-value pairs
            key, value = line.split("=", 1)
            key = key.strip()
            value = value.strip().strip('"').strip("'")  # remove quotes if present
            if key == "file_name":
                fname = value
            elif key == "tournament_name":
                t_name = value

    return fname, t_name


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

    fname, tournament_name = read_config()

    bus = EventBus()

    gui = GUI(bus, tournament_name)
    database = Database(bus, fname)
    match = Match(bus)

    # Main entry point
    database.load_tournament_list()
