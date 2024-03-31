"""Program constants, such as file paths."""
import pathlib


FOLDER = pathlib.Path(__file__).parent.parent
DATA_FOLDER = FOLDER / "data"
SNAPSHOT_FOLDER = DATA_FOLDER / "snapshots"

SCRAPE_LOG_FILE = DATA_FOLDER / "scrape.log"
COURSES_FILE = DATA_FOLDER / "_courses.json"
