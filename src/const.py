"""Program constants, such as file paths."""
import pathlib


FOLDER = pathlib.Path(__file__).parent.parent

BIN_FOLDER = FOLDER / "bin"
LATO_FONT_FILE = BIN_FOLDER / "Lato.ttf"
ICON_FILE = BIN_FOLDER / "icon.png"

DATA_FOLDER = FOLDER / "data"
SNAPSHOT_FOLDER = DATA_FOLDER / "snapshots"
SCRAPE_LOG_FILE = DATA_FOLDER / "scrape.log"
EMAIL_LOG_FILE = DATA_FOLDER / "email.log"
COURSES_FILE = DATA_FOLDER / "_courses.json"
CUPS_FILE = DATA_FOLDER / "_cups.json"
EMAIL_CONFIG_FILE = DATA_FOLDER / "email_config.json"
