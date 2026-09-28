"""Install contract: the documented install must produce a working dashboard.

Regression for a defect found by the real-browser audit: the README installed
starlette, uvicorn and pydantic only. uvicorn then has no websocket library,
answers /ws/fleet with 404, and the dashboard sits on "Disconnected" with an
empty map - while every in-process test still passed, because TestClient
does not use uvicorn's websocket stack.
"""

from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_readme_install_line_includes_a_websocket_library():
    text = (ROOT / "README.md").read_text()
    lines = [l for l in text.splitlines() if l.strip().startswith("pip install starlette")]
    assert lines, "README must document the runtime install line"
    assert all("websockets" in l for l in lines), lines


def test_pyproject_declares_websockets():
    text = (ROOT / "pyproject.toml").read_text()
    assert re.search(r'"websockets', text)


def test_run_sh_checks_for_a_websocket_library():
    text = (ROOT / "run.sh").read_text()
    assert "import websockets" in text and "import wsproto" in text
