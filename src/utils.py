"""Utility functions throughout the project."""
import ast
import datetime as dt
import hashlib
import json
import pathlib
import sqlite3
from dataclasses import dataclass

from const import COURSES_FILE, CUPS_FILE, SNAPSHOT_FOLDER


# Integrity hashes for course/cup data (prevents modification).
COURSES_DATA_HASH = "0e11659dda7756482c81fdc5bc3ca0d2aeb48a4f7a1daeb31487e35140fd1d73"
CUPS_DATA_HASH = "17d47550bc9d2dddeeabfd579709386df957ad8367d7532b60d7410647b61306"
BABY_PARK = "GCN Baby Park"
# Maximum number of recent snapshots to store.
MAX_RECENT_SNAPSHOTS = 5


def get_courses() -> list[str]:
    """Returns the list of courses."""
    with COURSES_FILE.open("r", encoding="utf8") as f:
        courses = json.load(f)
    data_hash = hashlib.sha256(
        str(courses).encode(), usedforsecurity=False).hexdigest()
    if data_hash != COURSES_DATA_HASH:
        raise ValueError("Invalid courses data file.")
    return courses


def get_cups() -> list[str]:
    """Returns the list of cups."""
    with CUPS_FILE.open("r", encoding="utf8") as f:
        cups = json.load(f)
    data_hash = hashlib.sha256(
        str(cups).encode(), usedforsecurity=False).hexdigest()
    if data_hash != CUPS_DATA_HASH:
        raise ValueError("Invalid cups data file.")
    return cups


COURSES = get_courses()
CUPS = get_cups()


def get_lap_count(course: str) -> int:
    """
    Returns the number of laps a course has
    This is to handle the Baby Park special case of 7 laps.
    """
    return 7 if course == BABY_PARK else 3


def ms_to_finish_time(ms: int) -> str:
    """Converts milliseconds to M:SS.mmm e.g. 5128 -> 0:05.128"""
    minutes, ms = divmod(ms, 60000)
    seconds, ms = divmod(ms, 1000)
    return f"{minutes}:{str(seconds).zfill(2)}.{str(ms).zfill(3)}"


@dataclass
class Record:
    """Represents a world record for a particular course and cubic capacity."""
    course: str
    is200: bool
    date: dt.date | None
    time: int # milliseconds
    player: str
    country: str
    days: int
    lap_times: tuple[int] | None # all milliseconds
    coins: tuple[int] | None
    mushrooms: tuple[int] | None
    character: str | None
    kart: str | None
    tyres: str | None
    glider: str | None
    video_link: str | None


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


def save_records(records: list[Record]) -> None:
    """Saves all records to a snapshot database."""
    # Use UTC to keep things consistent
    date_time_string = dt.datetime.utcnow().isoformat().replace(":", "")
    database_path = SNAPSHOT_FOLDER / f"{date_time_string}.db"
    with Database(database_path) as cursor:
        cursor.execute(
            """
            CREATE TABLE data(
                course INTEGER, is200 INTEGER, date DATE, time INTEGER,
                player TEXT, country TEXT, days INTEGER, lap_times TEXT,
                coins TEXT, mushrooms TEXT, character TEXT, kart TEXT,
                tyres TEXT, glider TEXT, video_link TEXT
            )""")
        save_records = []
        for record in records:
            course_id = COURSES.index(record.course)
            lap_times = (
                None if record.lap_times is None else str(record.lap_times))
            coins = None if record.coins is None else str(record.coins)
            mushrooms = (
                None if record.mushrooms is None else str(record.mushrooms))
            save_record = (
                course_id, record.is200, record.date, record.time,
                record.player, record.country, record.days,
                lap_times, coins, mushrooms, record.character, record.kart,
                record.tyres, record.glider, record.video_link)
            save_records.append(save_record)
        cursor.executemany(
            f"""
            INSERT INTO data VALUES ({','.join('?' * len(save_records[0]))})
            """, save_records)
        

def remove_old_snapshots() -> None:
    """Remove least recent snapshots to preserve storage space."""
    snapshots = sorted(SNAPSHOT_FOLDER.rglob("*.db"))
    for snapshot in snapshots[:-MAX_RECENT_SNAPSHOTS]:
        snapshot.unlink(missing_ok=True)


def get_most_recent_snapshot() -> pathlib.Path:
    """Returns the file path of the most recent snapshot."""
    try:
        return sorted(SNAPSHOT_FOLDER.rglob("*.db"))[-1]
    except IndexError:
        raise IndexError(
            "No records snapshots found. Please run the scraping script.")


def get_most_recent_snapshot_date_time() -> dt.datetime:
    """Returns the date/time of the most recent snapshot."""
    snapshot = get_most_recent_snapshot()
    filename = snapshot.stem
    return dt.datetime.strptime(filename, "%Y-%m-%dT%H%M%S.%f")


def process_db_record(record: tuple) -> Record:
    """Converts a database record into a dataclass object."""
    course_id, is200, date, time_, player, country, days = record[:7]
    course = COURSES[course_id]
    if date is not None:
        date = dt.date.fromisoformat(date)
    lap_times = ast.literal_eval(record[7] or "None")
    coins = ast.literal_eval(record[8] or "None")
    mushrooms = ast.literal_eval(record[9] or "None")
    character, kart, tyres, glider, video_link = record[10:]
    record = Record(
        course, is200, date, time_, player, country, days, lap_times,
        coins, mushrooms, character, kart, tyres, glider, video_link)
    return record


def get_course_cc_records(
    course: str, is200: bool,
    min_date: dt.date | None, max_date: dt.date | None
) -> list[Record]:
    """
    Returns a list containing all world records
    for a given course/CC combination.
    """
    course_id = COURSES.index(course)
    database_path = get_most_recent_snapshot()
    params = [course_id, is200]
    where_parts = ["course = ?", "is200 = ?"]
    if min_date is not None:
        params.append(min_date)
        where_parts.append("date >= ?")
    if max_date is not None:
        params.append(max_date)
        where_parts.append("date <= ?")
    with Database(database_path) as cursor:
        db_records = cursor.execute(
            f"SELECT * FROM data WHERE {' AND '.join(where_parts)}",
            params).fetchall()
    records = list(map(process_db_record, db_records))
    return records


def get_cc_records(
    is200: bool, min_date: dt.date | None, max_date: dt.date | None
) -> None:
    """Returns all records from all courses for a given cubic capacity."""
    database_path = get_most_recent_snapshot()
    params = [is200]
    where_parts = ["is200 = ?"]
    if min_date is not None:
        params.append(min_date)
        where_parts.append("date >= ?")
    if max_date is not None:
        params.append(max_date)
        where_parts.append("date <= ?")
    with Database(database_path) as cursor:
        db_records = cursor.execute(
            f"SELECT * FROM data WHERE {' AND '.join(where_parts)}",
            params).fetchall()
    records = list(map(process_db_record, db_records))
    return records


def get_150cc_records(
    min_date: dt.date | None, max_date: dt.date | None
) -> list[Record]:
    """Returns all 150cc records from all courses within a given date range."""
    return get_cc_records(False, min_date, max_date)


def get_200cc_records(
    min_date: dt.date | None, max_date: dt.date | None
) -> list[Record]:
    """Returns all 200cc records from all courses within a given date range."""
    return get_cc_records(True, min_date, max_date)


def get_uniques(records: list[Record]) -> tuple[set]:
    """
    Returns unique players, countries, characters, karts, tyres and gliders.
    They are all returned as sets, so order is not preserved.
    """
    unique_players = set(record.player for record in records)
    unique_countries = set(record.country for record in records)
    # Ignore 'None'
    unique_characters = set(
        record.character for record in records if record.character)
    unique_karts = set(
        record.kart for record in records if record.kart)
    unique_tyres = set(
        record.tyres for record in records if record.tyres)
    unique_gliders = set(
        record.glider for record in records if record.glider)
    return (
        unique_players, unique_countries, unique_characters,
        unique_karts, unique_tyres, unique_gliders)
