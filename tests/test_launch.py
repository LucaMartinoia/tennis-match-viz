from pathlib import Path
import shutil
import subprocess
import sys

import pytest

ROOT = Path(__file__).resolve().parents[1]
STARTUP_TIMEOUT = 10


def test_app_py_starts_as_python_program():
    _assert_app_stays_running(
        [sys.executable, "app.py", "--config"],
    )


def test_installed_cli_starts():
    executable = shutil.which("tennis-viz")
    assert (
        executable
    ), "tennis-viz CLI not found; install the package with: pip install -e ."

    _assert_app_stays_running(
        f'"{executable}" --config',
        shell=True,
    )


def _assert_app_stays_running(command, *, shell=False):
    process = subprocess.Popen(
        command,
        cwd=ROOT,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        shell=shell,
    )

    try:
        process.wait(timeout=STARTUP_TIMEOUT)
    except subprocess.TimeoutExpired:
        return
    finally:
        if process.poll() is None:
            process.terminate()
            process.wait(timeout=5)

    if process.returncode == 4551:
        pytest.skip("Windows Device Guard blocked the installed console executable")
    assert process.returncode == 0, process.stderr.read()
