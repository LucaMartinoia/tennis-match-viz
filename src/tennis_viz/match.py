from tennis_viz.engine import Engine
from tennis_viz.parser import Parser
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
        # Initialize Event bus
        self.bus = bus
        self.bus.subscribe("change-point", self.on_change_point)
        self.bus.subscribe("match-df-ready", self.set_df)
        self.bus.subscribe("animation-finished", self.on_animation_finished)
        self.bus.subscribe("animation-interrupted", self.on_animation_interrupted)
        # Load the match dataframe
        self.match_df = df
        self.point_in_game = 0  # To compute the quadrant of the server
        self.point = 1  # Current point in match
        self.engine = Engine()
        self.parser = Parser(self.engine)
        self.autoplay = True

    def set_df(self, match_df) -> None:
        """
        Set the match dataframe.
        """
        # Set new dataframe
        self.match_df = match_df
        # Set to first point in
        first_index = self.match_df.index[0]
        self.set_point(first_index)

    def _point_trajectory(self) -> None:
        """
        Entry point to compute the point trajectory.
        """
        # Gather point data
        point_data = PointData(
            first=self.match_df.loc[self.point, "1st"],
            second=self.match_df.loc[self.point, "2nd"],
            point=self.point_in_game,
            server=self.match_df.loc[self.point, "Svr"],
            righthand1=True,
            righthand2=True,
        )
        # Reset the state of engine
        self.engine.reset()
        # Compute the point trajectory
        result = self.parser.run_point(point_data)
        if result:
            # If trajectory is computed correctly, emit it
            self.bus.emit("trajectory-ready", traj=self.trajectory)
        else:
            # Otherwise, skip to next point
            self.bus.emit(
                "console-print",
                text=f"Point {self.point} information is missing. Skipping to the next point.",
            )
            self.bus.emit("change-point", point="next")

    @property
    def trajectory(self):
        """
        Getter method for the full trajectory
        """
        return self.engine.traj

    def set_point(self, point: int) -> None:
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
        # Callback to update score on the GUI
        self.bus.emit("update-score", score=self.get_score_data())
        self.bus.emit("point-data-ready", data=self.get_point_data())
        # Compute the point trajectory
        self._point_trajectory()

    def on_change_point(self, point: str) -> None:
        """
        Callback method to change point GUI buttons.

        Change the current point and compute the trajectory.
        """
        if self.match_df is None or self.match_df.empty:
            return  # Nothing to do if no match loaded
        if point == "first":
            new_point = self.match_df.index[0]
        elif point == "previous":
            new_point = self.point - 1
        elif point == "next":
            new_point = self.point + 1
        elif point == "last":
            new_point = self.match_df.index[-1]
        # Bounds check
        if 1 <= new_point <= len(self.match_df):
            self.set_point(new_point)

    def on_animation_finished(self) -> None:
        """
        Callback function to when the GUI completes the animation.
        """
        # If this was the last point in the match, update the display to
        # show the final match score (attribute the last point to the winner)
        try:
            if self.match_df is not None and not self.match_df.empty:
                last_index = self.match_df.index[-1]
                if self.point == last_index:
                    set_scores, pts1, pts2, server = self.get_score_data()
                    # Apply the last point to the winner (PtWinner column)
                    row = self.match_df.loc[self.point]
                    pt_winner = int(row.get("PtWinner", 0) or 0)
                    if pt_winner in (1, 2) and set_scores:
                        final = [list(s) for s in set_scores]
                        idx = 0 if pt_winner == 1 else 1
                        final[-1][idx] += 1
                        final_tuples = [tuple(x) for x in final]
                        # After the game point, points reset to 0-0
                        self.bus.emit("update-score", score=(final_tuples, "0", "0", server))
        except Exception:
            # Be permissive: don't block animation flow on score update errors
            pass

        # If animation is complete, move to next point automatically
        if self.autoplay:
            self.bus.emit("change-point", point="next")

    def on_animation_interrupted(self) -> None:
        """
        Callback function to when the GUI is interrupted during animation.
        """
        # Resend trajectory for current point
        self.bus.emit("trajectory-ready", traj=self.trajectory)

    def get_score_data(self):
        """
        Get current point score for the GUI.
        """
        # If data is missing, return an empty set score and point score.
        if self.match_df is None or self.match_df.empty:
            return [], "0", "0", 0

        row = self.match_df.loc[self.point]
        pts_str = str(row.get("Pts", "0-0"))
        server = row.get("Svr", 0)
        try:
            pts_srv, pts_def = pts_str.split("-")
            if server == 1:
                pts1, pts2 = pts_srv, pts_def
            elif server == 2:
                pts1, pts2 = pts_def, pts_srv
            else:
                # Unknown server
                pts1, pts2 = pts_srv, pts_def
        except ValueError:
            self.bus.emit("console-print", text=f"Score data is missing: {pts_str}")
            pts1, pts2 = 0, 0

        # Set1/Set2 are set totals, while Gm1/Gm2 are the game totals in
        # the current set. Reconstruct completed set scores from the rows
        # leading up to the current point. Detect tie-breaks and report
        # final set scores as 7-6 / 6-7 when appropriate.
        set_scores = []
        previous_set = (0, 0)
        previous_row = None
        for _, historical_row in self.match_df.loc[: self.point].iterrows():
            current_set = (
                int(historical_row.get("Set1", 0)),
                int(historical_row.get("Set2", 0)),
            )
            if previous_row is not None and current_set != previous_set:
                # Last row of the previous set is in previous_row
                gm1 = int(previous_row.get("Gm1", 0))
                gm2 = int(previous_row.get("Gm2", 0))
                # Detect tie-break: both games 6-6 and TbSet flagged
                try:
                    tbflag = bool(previous_row.get("TbSet", False))
                except Exception:
                    tbflag = False
                if gm1 == 6 and gm2 == 6 and tbflag:
                    # Determine which player won the set by comparing set totals
                    if current_set[0] > previous_set[0]:
                        set_scores.append((7, 6))
                    else:
                        set_scores.append((6, 7))
                else:
                    set_scores.append((gm1, gm2))
            previous_set = current_set
            previous_row = historical_row

        # Current (live) set game counts
        set_scores.append((int(row.get("Gm1", 0)), int(row.get("Gm2", 0))))
        return set_scores, pts1, pts2, server

    def get_point_data(self):
        """
        Get current point data for the GUI.
        """
        row = self.match_df.loc[self.point]
        second = False if row["2nd"] else True
        # Find aces
        ace = 0
        if row["1st"] and row["1st"][0] and row["1st"][0][-1] == "*":
            ace = 1
        elif row["2nd"] and row["2nd"][0] and row["2nd"][0][-1] == "*":
            ace = 2
        pt_winner = row["PtWinner"]
        # Return point data
        return self.point, second, ace, pt_winner

    def reset_all(self) -> None:
        """
        Reset all data and the engine.
        """
        self.engine.reset()
        first_index = self.match_df.index[0]
        self.set_point(first_index)
