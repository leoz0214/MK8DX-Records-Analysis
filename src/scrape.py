"""
Scrapes all 196 pages from https://mkwrs.com/mk8dx/, scraping each WR as
seen in the History sections, and save the information into a database.
"""
import datetime as dt
import logging
import time
import urllib.parse
from dataclasses import dataclass
from timeit import default_timer as timer

import lxml
import requests as rq
from bs4 import BeautifulSoup

from const import SNAPSHOT_FOLDER, SCRAPE_LOG_FILE
from utils import get_courses, get_lap_count, Database


URL = "https://mkwrs.com/mk8dx/display.php"
SECONDS_PER_SCRAPE = 2
MAX_REQUEST_ATTEMPTS = 3
EXPECTED_COLUMNS = 14
BABY_PARK_TOP_EXPECTED_COLUMNS = 15


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


def get_soup(course: str, is200: bool) -> BeautifulSoup:
    """
    Sends a request to the course/CC page, fetches the response HTML document,
    and returns a BeautifulSoup object ready for data extraction.
    """
    params = {"track": "+".join(course.split())}
    if is200:
        params["m"] = "200"
    query_string = "&".join(f"{key}={val}" for key, val in params.items())
    attempts = MAX_REQUEST_ATTEMPTS
    while True:
        try:
            response = rq.get(f"{URL}?{query_string}")
            if response.status_code != 200:
                raise RuntimeError(f"Status code {response.status_code}")
            return BeautifulSoup(response.text, "lxml")
        except Exception as e:
            attempts -= 1
            if not attempts:
                raise e
            time.sleep(1)


def get_common_data(data, lap_count: int = 3) -> tuple:
    """Returns the common data for normal courses and Baby Park."""
    try:
        date = dt.date.fromisoformat(data[0].text)
    except ValueError:
        date = None
    time_string = data[1].text
    minutes, seconds_ms = time_string.split("'")
    seconds, milliseconds = seconds_ms.split('"')
    time_ = (
        int(minutes) * 60 * 1000 + int(seconds) * 1000 + int(milliseconds))
    player = urllib.parse.unquote(
        data[2].find(
            "a", href=lambda href: href and "?player=" in href)["href"]
    ).split("=")[-1]
    country = data[3].find("img")["title"]
    days_string = data[4].text
    days = int(days_string) if days_string != "<1" else 0
    lap_times = ()
    for i in range(5, 5 + lap_count):
        lap_string = data[i].text
        if lap_string == "-":
            # Missing lap data
            lap_times = None
            break
        lap_times += (round(float(lap_string) * 1000),)
    try:
        coins = tuple(map(int, data[5 + lap_count].text.split("-")))
    except ValueError:
        coins = None
    return date, time_, player, country, days, lap_times, coins


def scrape_baby_park(course: str, is200: bool, table) -> list[Record]:
    """
    The Baby Park table is unique as per the course...
    specialised code to scrape it correctly.
    """
    records = []
    rows = table.find_all("tr")
    i = 0
    while i < len(rows) - 1:
        top_row = rows[i]
        top_row_data = top_row.find_all("td")
        i += 1
        if len(top_row_data) != BABY_PARK_TOP_EXPECTED_COLUMNS:
            continue
        date, time_, player, country, days, lap_times, coins = (
            get_common_data(top_row_data, 7))
        bottom_row = rows[i]
        bottom_row_data = bottom_row.find_all("td")
        try:
            mushrooms = tuple(map(int, bottom_row_data[0].text.split("-")))
        except ValueError:
            mushrooms = None
        character_string = top_row_data[13].text
        character = character_string if character_string != "-" else None
        kart_string = top_row_data[14].text
        kart = kart_string if kart_string != "-" else None
        tyres_string = bottom_row_data[1].text
        tyres = tyres_string if tyres_string != "-" else None
        glider_string = bottom_row_data[2].text
        glider = glider_string if glider_string != "-" else None
        record = Record(
            course, is200, date, time_, player, country, days,
            lap_times, coins, mushrooms, character, kart, tyres, glider)
        records.append(record)
    return records


def scrape_course(course: str, is200: bool) -> list[Record]:
    """Returns a list of parsed world records for a given course (150/200cc)"""
    soup = get_soup(course, is200)
    table = soup.find("h2", string="History").find_next_sibling("table")
    lap_count = get_lap_count(course)
    if lap_count == 7:
        return scrape_baby_park(course, is200, table)
    records = []
    for row in table.find_all("tr"):
        data = row.find_all("td")
        if len(data) != EXPECTED_COLUMNS:
            # Not a world record column, something else e.g. headings.
            continue
        date, time_, player, country, days, lap_times, coins = (
            get_common_data(data))
        try:
            mushrooms = tuple(map(int, data[6 + lap_count].text.split("-")))
        except ValueError:
            mushrooms = None
        character_string = data[7 + lap_count].text
        character = character_string if character_string != "-" else None
        kart_string = data[8 + lap_count].text
        kart = kart_string if kart_string != "-" else None
        tyres_string = data[9 + lap_count].text
        tyres = tyres_string if tyres_string != "-" else None
        glider_string = data[10 + lap_count].text
        glider = glider_string if glider_string != "-" else None
        record = Record(
            course, is200, date, time_, player, country, days,
            lap_times, coins, mushrooms, character, kart, tyres, glider)
        records.append(record)
    return records


def save(records: list[Record]) -> None:
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
                tyres TEXT, glider TEXT
            )""")
        save_records = []
        courses = get_courses()
        for record in records:
            course_id = courses.index(record.course)
            lap_times = (
                None if record.lap_times is None else str(record.lap_times))
            coins = None if record.coins is None else str(record.coins)
            mushrooms = (
                None if record.mushrooms is None else str(record.mushrooms))
            save_record = (
                course_id, record.is200, record.date, record.time,
                record.player, record.country, record.days,
                lap_times, coins, mushrooms, record.character, record.kart,
                record.tyres, record.glider)
            save_records.append(save_record)
        cursor.executemany(
            f"""
            INSERT INTO data VALUES ({','.join('?' * len(save_records[0]))})
            """, save_records)


def main() -> None:
    """Main procedure of the program."""
    SNAPSHOT_FOLDER.mkdir(parents=True, exist_ok=True)
    logging.basicConfig(
        handlers=(
            logging.FileHandler(SCRAPE_LOG_FILE), logging.StreamHandler()),
        encoding="utf8", level=logging.INFO,
        format= "%(asctime)s: %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S")
    courses = get_courses()
    records = []
    for course in courses:
        for cc in (150, 200):
            start = timer()
            try:
                course_cc_records = scrape_course(course, is200=(cc == 200))
                records.extend(course_cc_records)
                logging.info(f"Successfully scraped {course} {cc}cc.")
            except Exception as e:
                logging.critical(
                    f"Failed to scrape {course} {cc}cc: {e} [Terminating].")
                return
            stop = timer()
            time.sleep(max(SECONDS_PER_SCRAPE - (stop - start), 0))
    save(records)
    logging.info("Successfully saved all records to database.")


if __name__ == "__main__":
    main()
