from src.engine import Engine
from src.parser import Parser
import pandas as pd
from dataclasses import dataclass

"""
This module manages the core logic: it takes the match database and,
for each point, computes the full trajectory of the ball.

TO DO:
- Enrich method
- Fix boolean returns
"""


@dataclass
class PointData:
    first: str
    second: str
    point: int
    server: int
    righthand1: bool = True
    righthand2: bool = True


class Match:
    """
    The match class parses shot data into geometric quantities.
    """

    def __init__(self, bus, df=pd.DataFrame()):
        """
        Loads the match data and keep track of points.
        """
        # Load the match dataframe
        self.match_df = df
        self.point_in_game = 0  # To compute the quadrant of the server
        self.point = 1  # Current point in match
        self.engine = Engine()
        self.parser = Parser(self.engine)
        self.bus = bus
        self.bus.subscribe("change-point", self.on_change_point)

    def select_df(self, match_df):
        """
        Setter function for the match dataframe.
        """
        self.match_df = match_df

    def point_trajectory(self) -> None:
        """
        Entry point to compute the point trajectory.
        """
        point_data = PointData(
            first=self.match_df.loc[self.point, "1st"],
            second=self.match_df.loc[self.point, "2nd"],
            point=self.point_in_game,
            server=self.match_df.loc[self.point, "Svr"],
            righthand1=True,
            righthand2=True,
        )
        result = self.parser.run_point(point_data)
        # if not result:
        #    self.next_point()
        self.bus.emit("trajectory", traj=self.trajectory)

    @property
    def trajectory(self):
        """
        Getter method for the full trajectory
        """
        return self.engine.traj

    def select_point(self, point: int) -> None:
        """
        Setter method for the point in the match.
        Also updates point_in_game.
        """
        # Assign new point
        self.point = point

        # Current games
        gm1 = self.match_df.loc[self.point, "Gm1"]
        gm2 = self.match_df.loc[self.point, "Gm2"]

        # Find first point in the current game looping backward
        i = self.point - 1
        count = 0
        while (
            i >= 1
            and self.match_df.loc[i, "Gm1"] == gm1
            and self.match_df.loc[i, "Gm2"] == gm2
        ):
            count += 1
            i -= 1

        # 0-based count within the game
        self.point_in_game = count
        self.point_trajectory()

    def on_change_point(self, next: bool):
        if self.match_df is None or self.match_df.empty:
            return  # nothing to do if no match loaded

        new_point = self.point + 1 if next else self.point - 1

        # bounds check
        if 1 <= new_point <= len(self.match_df):
            self.select_point(new_point)
            self.bus.emit("update-score", score=self.update_score_data())
        # else do nothing (self.bus.emit("console-print", text="Point missing."))

    def update_score_data(self):
        if self.match_df is None or self.match_df.empty:
            return 0, 0, 0, 0, 0, 0

        row = self.match_df.loc[self.point]

        set1 = row.get("Set1", 0)
        set2 = row.get("Set2", 0)
        gm1 = row.get("Gm1", 0)
        gm2 = row.get("Gm2", 0)
        pts_str = str(row.get("Pts", "0-0"))
        try:
            pts1_str, pts2_str = pts_str.split("-")
            pts1, pts2 = int(pts1_str), int(pts2_str)
        except ValueError:
            pts1, pts2 = 0, 0
        return set1, set2, gm1, gm2, pts1, pts2

    def reset_all(self) -> None:
        """
        Setter method for the point in the match.
        """
        self.point_in_game = 0  # To compute the quadrant of the server
        self.point = 1  # Point under consideration
        self.engine.reset()

    def enrich(self):
        """
        This method should enrich the dataframe with extra
        info scraped from wikipedia.

        Specifically: handedness of the two players.
        """
        pass
