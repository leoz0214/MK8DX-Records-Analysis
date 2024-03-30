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
from utils import get_courses, get_lap_count


URL = "https://mkwrs.com/mk8dx/display.php"
SECONDS_PER_SCRAPE = 2
MAX_REQUEST_ATTEMPTS = 3


@dataclass
class Record:
    """Represents a world record for a particular course and cubic capacity."""
    course: str
    is200: bool
    date: dt.date | None
    time: int # milliseconds
    player: str
    nation: str
    days: int
    lap_times: list[int] | None # all milliseconds
    coins: list[int] | None
    mushrooms: list[int] | None
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


def scrape_course(course: str, is200: bool) -> list[Record]:
    """Returns a list of parsed world records for a given course (150/200cc)"""
    soup = get_soup(course, is200)
    table = soup.find("h2", string="History").find_next_sibling("table")
    lap_count = get_lap_count(course)
    records = []
    for row in table.find_all("tr"):
        expected_columns = 11 + lap_count
        data = row.find_all("td")
        if len(data) != expected_columns:
            # Not a world record column, something else e.g. headings.
            continue
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
        # TODO - rest of the stats


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
                records.extend(scrape_course(course, is200=(cc == 200)))
                logging.info(f"Successfully scraped {course} {cc}cc.")
            except Exception as e:
                logging.critical(
                    f"Failed to scrape {course} {cc}cc: {e} [Terminating].")
                return
            stop = timer()
            time.sleep(max(SECONDS_PER_SCRAPE - (stop - start), 0))


if __name__ == "__main__":
    main()
