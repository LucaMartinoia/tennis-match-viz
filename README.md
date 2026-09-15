# Tennis Match Visualizer

Tennis Match Visualizer is a lightweight and interactive application that lets you experience professional tennis matches point by point. It leverages shot-by-shot data from the [Match Charting Project](https://www.tennisabstract.com/blog/2015/09/23/the-match-charting-project-quick-start-guide/), a remarkable initiative that systematically records pro tennis matches in a standardized format, making it possible to analyze patterns and strategies.

The app reads CSV files from the Match Charting Project and brings the match to life using [VPython](https://www.glowscript.org/docs/VPythonDocs/index.html), a simple 3D animation library. While the data is not precise enough for exact meter-by-meter reconstruction of every shot, the main goal is to provide a clear and engaging visual impression of the flow, positioning, and dynamics of each point.

<p align="center">
    <img src="assets/doc.png" style="width: 60%;">
</p>

Within the application, you can:

- Select the tournament and match to visualize
- Run matches point by point, with full animation
- Control playback with play/pause, slow motion, and point navigation buttons
- Switch between day and night modes for the court
- Interact with the camera: zoom, rotate, and move freely
- View a live score table and follow the match progression

This project started as a hands-on exploration of Python, GUI development, and 3D animation. It continues to be a space for experimenting with visualizations and creating an engaging way to explore tennis match data.

## Installation and usage

1.  Install the package and its runtime dependencies (Python 3):

        pip install -e .

2.  Run the application from the command line:

        tennis-viz --config

    You can also start it directly from the repository:

        python app.py --config

3.  The CSV file with the match list can be found in `/data`. You can add more CSV files from the Match Charting Project database.

4.  To select a given file or default tournament, edit `config.txt`.

## Running tests

Install the development and test dependencies:

        pip install -r requirements.txt

Run the full test suite:

        python -m pytest

Run only the application startup tests:

        python -m pytest -q tests/test_launch.py

## Notes

- Since the data is not fully detailed, some shot trajectories are randomized to fill in missing information.
- The application is best used for exploring and understanding match dynamics, rather than precise statistics.
- The interface is simple and designed for clarity, with controls and score displays integrated around the 3D court.
- Some bits are still work in progress.
