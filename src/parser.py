import pandas as pd
from pathlib import Path

"""
This module should read the CSV file as pandas dataframe, look for the rows
associated with the game of interest, and convert the data in a format that
can be passed to the dynamics and UI.

TO DO:
- Compute correct Gm missing values
- Check surface depending on tournament
"""


class Parser:
    """
    Load the database and extract match data.
    """

    def __init__(self, fname: str = "charting-m-points-2020s.csv"):
        """
        Load the database from the CSV file.
        """
        # Directories containing this file and root
        here = Path(__file__).resolve().parent
        root = here.parent
        fpath = root / "data" / fname
        # Loading data
        try:
            self.df = pd.read_csv(
                fpath,
                dtype={
                    "match_id": "string",
                    "Pt": "int64",
                    "Set1": "int64",
                    "Set2": "int64",
                    "Gm1": "int64",
                    "Gm2": "Int64",
                    "PtWinner": "int64",
                    "Pts": "string",
                    "TbSet": "string",
                    "1st": "string",
                    "2nd": "string",
                    "Notes": "string",
                },
                keep_default_na=True,
            )
        except FileNotFoundError:
            raise FileNotFoundError(f"CSV file not found at {fpath}")
        except pd.errors.DtypeWarning as e:
            print(f"Warning while loading CSV: {e}")
        except Exception as e:
            raise RuntimeError(f"Error loading CSV file: {e}")

        # Sanitizing missing entries
        self._fix_missing_values()
        # Expand the database withn useful fields
        self.expand_match_id_fields()

    def _fix_missing_values(self):
        """
        Clean dataframe from incorrect entries.
        """
        self.df[["TbSet", "Gm2"]] = self.df[["TbSet", "Gm2"]].ffill()

    def tournaments_list(self):
        """
        Return the full list of unique tournaments.

        str: "tournament_name year"
        """
        return self.df["tournament_full"].unique()

    def matches_list(self, tournament: str):
        """
        Return the full list of matches for a given tournament.

        str: "round - p1_name vs p2_name"
        """
        df_t = self.df[self.df["tournament_full"] == tournament]
        return df_t["round"].unique()

    def match_data(self, tournament: str, match: str):
        """
        Return dataframe with list of points in useful form
        """
        # Find the match of interest
        df_t = self.df[
            (self.df["tournament_full"] == tournament) & (self.df["round"] == match)
        ]
        if len(df_t["match_id"].unique()) != 1:
            print("Tournament and round returned multiple matches.")

        # Filter the data we need
        df_t = df_t[
            ["Pt", "Set1", "Set2", "Gm1", "Gm2", "Pts", "Svr", "1st", "2nd", "PtWinner"]
        ]
        df_t = df_t.set_index("Pt")

        return df_t

    def format_point(self, point):
        pass

    def expand_match_id_fields(self):
        """
        Parse match_id for every row and expand the dataframe with:
        - date (YYYY-MM-DD)
        - tournament name
        - round (round - p1 vs p2)
        - p1 name
        - p2 name
        - tournament full (tournament+year)
        """
        # Split match_id into its 6 components
        parts = self.df["match_id"].str.split("-", expand=True)

        # Convert YYYYMMDD → YYYY-MM-DD
        dr = parts[0].astype(str)
        self.df["date"] = (
            dr.str.slice(0, 4) + "-" + dr.str.slice(4, 6) + "-" + dr.str.slice(6, 8)
        )

        # Clean player names
        self.df["p1"] = parts[4].str.split("_").str[1:].str.join(" ")
        self.df["p2"] = parts[5].str.split("_").str[1:].str.join(" ")

        # Combine fields for nicer grouping
        self.df["tournament_full"] = (
            parts[2].str.replace("_", " ") + " " + dr.str.slice(0, 4)
        )
        self.df["round"] = parts[3] + " - " + self.df["p1"] + " vs " + self.df["p2"]


parser = Parser()

df = parser.match_data("Australian Open 2021", "R128 - Sinner vs Shapovalov")

print(df.head(40))
