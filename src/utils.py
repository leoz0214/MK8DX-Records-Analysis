"""Utility functions throughout the project."""
import hashlib
import json
import pathlib
import sqlite3

from const import COURSES_FILE


# Integrity hash for course data (prevents modification).
COURSES_DATA_HASH = "de27fa10c283cc4990a78becc41fa9ca203254e910d5f4d2663d414c704cdc28"
BABY_PARK = "GCN Baby Park"


def get_courses() -> list[str]:
    """Returns the list of courses."""
    with COURSES_FILE.open("r", encoding="utf8") as f:
        courses = json.load(f)
    data_hash = hashlib.sha256(
        str(courses).encode(), usedforsecurity=False).hexdigest()
    if data_hash != COURSES_DATA_HASH:
        raise ValueError("Invalid courses data file.")
    return courses


def get_lap_count(course: str) -> int:
    """
    Returns the number of laps a course has
    This is to handle the Baby Park special case of 7 laps.
    """
    return 7 if course == BABY_PARK else 3


class Database:
    """Sqlite3 database wrapper."""

    def __init__(self, database_path: pathlib.Path) -> None:
        self.path = database_path

    def __enter__(self) -> sqlite3.Cursor:
        """Start of database processing context manager."""
        self.connection = sqlite3.connect(self.path)
        cursor = self.connection.cursor()
        return cursor
    
    def __exit__(self, exception: Exception | None, *_) -> None:
        """Context manager exited - commit if no error occurred."""
        if exception is None:
            self.connection.commit()
        self.connection.close()
        self.connection = None
