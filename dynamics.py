from vpython import canvas, box, color, vector, sphere, distant_light
import numpy as np
from court import coordinates
import csv
from types import SimpleNamespace


class Point:
    def __init__(self):
        self.court, self.single_court, self.serve_box = coordinates()

    def shot(self):
        pass

    def parser(self):
        pass


def match_id_parser(match_id):
    match_info = SimpleNamespace()
    try:
        date_raw, _, tournament, round, p1_raw, p2_raw = match_id.split("-")
    except ValueError:
        raise ValueError(f"Invalid match_id format: {match_id}")

    match_info.date = f"{date_raw[:4]}-{date_raw[4:6]}-{date_raw[6:]}"
    match_info.tournament = tournament
    match_info.round = round
    match_info.p1 = " ".join(p1_raw.split("_")[1:])
    match_info.p2 = " ".join(p2_raw.split("_")[1:])
    # TO DO: check surface depending on tournament
    return match_info


if __name__ == "__main__":
    points = []

    with open("games/sinner_test.csv", newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            match_info = match_id_parser(row["match_id"])
            point = SimpleNamespace(
                point_num=int(row["Pt"]),
                set_p1=int(row["Set1"]),
                set_p2=int(row["Set2"]),
                game_p1=int(row["Gm1"]),
                game_p2=int(row["Gm2"]),
                game_num=int(row["Gm#"]),
                server=int(row["Svr"]),
                first=row["1st"],
                second=row["2nd"],
                winner=int(row["PtWinner"]),
            )
            points.append(point)

    print(points[0])
