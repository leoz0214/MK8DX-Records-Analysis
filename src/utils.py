"""Utility functions throughout the project."""
import hashlib
import json

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
