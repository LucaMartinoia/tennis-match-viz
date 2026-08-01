from tennis_viz.database import Database
from tennis_viz.match import Match
from tennis_viz.gui_vpython import GUI
import os
import argparse


def parse_args():
    """
    Parse command line arguments.
    """
    parser = argparse.ArgumentParser(
        prog="tennis-viz",
        description="Visualize tennis matches from Match Charting Project data.",
    )

    parser.add_argument("file_name", nargs="?", help="CSV file to load directly")

    parser.add_argument(
        "--config",
        action="store_true",
        help="Load file and tournament name from config.txt",
    )

    return parser.parse_args()


def read_config():
    """
    Read the config.txt file.
    """
    fname = None
    t_name = None

    if not os.path.isfile("config.txt"):
        print("WARNING: config.txt file is missing.")
        return fname, t_name

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


def main():
    args = parse_args()

    if args.file_name:
        fname = args.file_name
        tournament_name = None
    else:
        fname, tournament_name = read_config()

    if fname is None:
        raise ValueError("No CSV file specified. Use a filename or --config.")

    bus = EventBus()

    gui = GUI(bus, tournament_name)
    database = Database(bus, fname)
    match = Match(bus)

    database.load_tournament_list()


if __name__ == "__main__":
    main()
