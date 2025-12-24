from src.engine import Engine
from src.parser import Parser
import pandas as pd
from dataclasses import dataclass

"""
This module manages the core logic: it takes the match database and,
for each point, computes the full trajectory of the ball.

TO DO:
- Enrich method
- Order functions
- Test functions
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

    def __init__(self, df=pd.DataFrame()):
        """
        Loads the match data and keep track of points.
        """
        # Load the match dataframe
        self.match_df = df
        self.point_in_game = 0  # To compute the quadrant of the server
        self.point = 1  # Current point in match
        self.engine = Engine()
        self.parser = Parser(self.engine)

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
        p1 = self.match_df.loc[self.point]["player 1"]
        p2 = self.match_df.loc[self.point]["player 2"]
        return p1, p2

    @property
    def trajectory(self):
        """
        Getter method for the full trajectory
        """
        return self.engine.traj

    def enrich(self):
        """
        This method should enrich the dataframe with extra
        info scraped from wikipedia.

        Specifically: handedness of the two players.
        """
        pass
