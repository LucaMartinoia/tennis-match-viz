from src.engine import Engine
from src.parser import Parser
import pandas as pd
from dataclasses import dataclass

"""
This module manages the core logic: it takes the match database and,
for each point, computes the full trajectory of the ball.
"""


@dataclass
class PointData:
    first: str
    second: str
    point: int
    server: int
    hand1: bool = True
    hand2: bool = True


class Match:
    """
    The match class parses shot data into geometric quantities.
    """

    def __init__(self, df=pd.DataFrame()):
        """
        Loads the match data and keep track of points.
        """
        # Load the match dataframe
        print("Loading match...")
        self.match_df = df
        self.point_in_game = 0  # To compute the quadrant of the server
        self.point = 1  # Point under consideration
        self.engine = Engine()  # One point per timestep
        self.parser = Parser(self.engine)
        self.point_data = PointData(
            first="",
            second="",
            point=self.point_in_game,
            server=0,
            hand1=True,
            hand2=True,
        )

    def point_trajectory(self):
        """
        Entry point to compute the point trajectory.
        """
        row = self.match_df.iloc[self.point]
        self.engine.reset()
        self.point_data.first = row["1st"]
        self.point_data.second = row["2nd"]
        self.point_data.point = self.point_in_game
        self.server = row["server"]
        result = self.parser.run_point(self.point_data)
        print(result)

    def select_point(self, point: int) -> None:
        """
        Setter method for the point in the match.
        Also updates point_in_game.
        """
        # Assign new point
        self.point = point

        # Current games
        idx = self.point - 1
        gm1 = self.match_df.iloc[idx]["Gm1"]
        gm2 = self.match_df.iloc[idx]["Gm2"]

        # Find first point in the current game looping backward
        i = idx
        count = 0
        while (
            self.match_df.iloc[i - 1]["Gm1"] == gm1
            and self.match_df.iloc[i - 1]["Gm2"] == gm2
        ):
            count += 1
            i -= 1

        # 0-based count within the game
        self.point_in_game = count

    def next_point(self) -> None:
        """
        Helper function to move to the next point if it exists.
        """
        if not (0 <= self.point < len(self.match_df)):
            return  # Point is out of bounds, exit early

        self.select_point(self.point + 1)

    def previous_point(self) -> None:
        """
        Helper function to move to the previous point if it exists.
        """
        if not (0 <= self.point < len(self.match_df)):
            return  # Point is out of bounds, exit early

        self.select_point(self.point - 1)

    def reset_all(self) -> None:
        """
        Setter method for the point in the match.
        """
        self.point_in_game = 0  # To compute the quadrant of the server
        self.point = 1  # Point under consideration
        self.engine.reset()

    def get_player_names(self):
        """
        Getter method for player names.
        """
        idx = self.point - 1
        p1 = self.match_df.iloc[idx]["player 1"]
        p2 = self.match_df.iloc[idx]["player 2"]
        return p1, p2

    @property
    def trajectory(self):
        """
        Getter method for the full trajectory
        """
        return self.engine.traj
