"""Build the static site into build/ (this is what GitHub Pages publishes).

    python freeze.py            # writes build/
    python freeze.py --serve    # also serves build/ on http://localhost:8000
"""
import shutil
import sys
from pathlib import Path

from flask_frozen import Freezer

from app import app, routed_pages

BUILD = Path(__file__).resolve().parent / "build"
app.config["FREEZER_DESTINATION"] = str(BUILD)
app.config["FREEZER_REMOVE_EXTRA_FILES"] = True
freezer = Freezer(app)


@freezer.register_generator
def page():
    for p in routed_pages():
        yield {"path": p.url.strip("/")}


if __name__ == "__main__":
    freezer.freeze()
    (BUILD / ".nojekyll").touch()
    print(f"built {len(list(BUILD.rglob('index.html')))} pages in {BUILD}")
    if "--serve" in sys.argv:
        import http.server
        import os
        os.chdir(BUILD)
        http.server.test(HandlerClass=http.server.SimpleHTTPRequestHandler, port=8000)
