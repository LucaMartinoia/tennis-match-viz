import pandas as pd
from pathlib import Path
import re

"""
This module reads the CSV file as pandas dataframe, look for the rows
associated with the match of interest, and convert the data in a format that
can be passed to the dynamics and UI.

TO DO:
- Compute correct Gm missing values
- Check court surface depending on tournament
"""


class Database:
    """
    Load the database and extract match data.
    """

    def __init__(self, fname: str = "charting-m-points-2020s.csv"):
        """
        Load, clean and prepare the dataframe.
        """
        # Load dataframe
        print(f"Loading data from {fname}...")
        self.df, result_str = self._load_csv(fname)
        # Sanitizing missing entries
        self._sanitize_df()
        # Expand the database withn useful fields
        self._expand_df_fields()
        print(result_str)
        # Tournament and match fields
        self.tournament = ""
        self.match = ""

    def _load_csv(self, fname: str):
        """
        Load the database from the CSV file.
        """
        # Directories containing this file and root
        here = Path(__file__).resolve().parent
        root = here.parent
        fpath = root / "data" / fname
        # Loading data
        try:
            df = pd.read_csv(
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

        return df, "Data loaded successfully."

    def _sanitize_df(self):
        """
        Clean dataframe from incorrect entries.
        """
        self.df[["TbSet", "Gm2"]] = self.df[["TbSet", "Gm2"]].ffill()

    def tournaments_list(self):
        """
        Return the full list of unique tournaments.

        str: "tournament_name year"
        """
        return self.df["tournament_full"].astype(str).unique().tolist()

    def set_tournament(self, tournament: str):
        """
        Set tournament field.
        """
        if tournament not in self.df["tournament_full"].values:
            raise ValueError(f"Tournament '{tournament}' not found in dataset.")
        self.tournament = tournament

    def set_match(self, match: str):
        """
        Set tournament field.
        """
        if match not in self.df["match"].values:
            raise ValueError(f"Tournament '{match}' not found in dataset.")
        self.match = match

    def matches_list(self, tournament: str = ""):
        """
        Return the full list of matches for a given tournament.

        str: "match - p1_name vs p2_name"
        """
        if tournament:
            self.set_tournament(tournament)
        df_t = self.df[self.df["tournament_full"] == self.tournament]
        return df_t["match"].astype(str).unique().tolist()

    def match_data(self, match: str = ""):
        """
        Return dataframe with list of points in useful form
        """
        if match:
            self.set_match(match)
        # Find the match of interest
        df_t = self.df[
            (self.df["tournament_full"] == self.tournament)
            & (self.df["match"] == self.match)
        ]
        if len(df_t["match_id"].unique()) != 1:
            return print("Tournament and match returned multiple matches.")

        # Filter the data we need
        df_t = df_t[
            ["Pt", "Set1", "Set2", "Gm1", "Gm2", "Pts", "Svr", "1st", "2nd", "PtWinner"]
        ]
        # Parse point strings
        df_t["1st"] = df_t["1st"].apply(self._format_point)
        df_t["2nd"] = df_t["2nd"].apply(self._format_point)
        # Use Pt as index
        df_t = df_t.set_index("Pt")

        return df_t

    def _format_point(self, point):
        """
        Reads the point rallys and convert them in lists
        of strings that can be used by the dynamics.
        """
        error = {"n", "w", "x", "d", "g", "e"}
        # Handle <NA> entries
        if pd.isna(point):
            return [""]

        # Split using your regex
        parts = re.findall(r"[A-Za-z][^A-Za-z]*|^[0-9]+", point)
        cleaned = []
        for p in parts:
            # drop approach marker
            p = p.replace("+", "")
            if p.startswith("c"):
                p = p[1:]  # remove leading "c"
            if p:  # keep only if non-empty
                cleaned.append(p)
        parts = cleaned

        # Annotate transitions
        for i in range(len(parts) - 1):
            parts[i] = parts[i] + parts[i + 1][0]

        # merge trailing error, for any length >= 2
        if len(parts) >= 2 and parts[-1][0] in error:
            parts[-2] += parts[-1][1:]
            parts.pop()

        return parts

    def _expand_df_fields(self):
        """
        Parse match_id for every row and expand the dataframe with:
        - date (YYYY-MM-DD)
        - tournament name
        - match (round - p1 vs p2)
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
        self.df["match"] = parts[3] + " - " + self.df["p1"] + " vs " + self.df["p2"]


if __name__ == "__main__":
    parser = Parser()

    parser.tournament = "Australian Open 2021"

    df = parser.match_data("R128 - Sinner vs Shapovalov")

    print(df.head())
