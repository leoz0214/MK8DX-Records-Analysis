"""
Scrapes all 196 pages from https://mkwrs.com/mk8dx/, scraping each WR as
seen in the History sections, and save the information into a database.
"""
import datetime as dt
import logging
import time
import urllib.parse
from timeit import default_timer as timer

import requests as rq
from bs4 import BeautifulSoup

from const import SNAPSHOT_FOLDER, SCRAPE_LOG_FILE
from utils import (
    COURSES, get_lap_count, Record, save_records, remove_old_snapshots)


URL = "https://mkwrs.com/mk8dx/display.php"
SECONDS_PER_SCRAPE = 2
MAX_REQUEST_ATTEMPTS = 3
EXPECTED_COLUMNS = 14
BABY_PARK_TOP_EXPECTED_COLUMNS = 15


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
            try:
                # Attempt to use LXML (more efficient)
                return BeautifulSoup(response.text, "lxml")
            except Exception:
                # Built-in HTML parser as fallback.
                return BeautifulSoup(response.text, "html.parser")
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
    video_link_a = data[1].find("a")
    video_link = video_link_a["href"] if video_link_a is not None else None
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
        if lap_string == "-" or not lap_string:
            # Missing lap data
            lap_times = None
            break
        lap_times += (round(float(lap_string) * 1000),)
    try:
        coins = tuple(map(int, data[5 + lap_count].text.split("-")))
        if len(coins) != lap_count:
            coins = None
    except ValueError:
        coins = None
    return date, time_, video_link, player, country, days, lap_times, coins


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
        date, time_, video_link, player, country, days, lap_times, coins = (
            get_common_data(top_row_data, 7))
        bottom_row = rows[i]
        bottom_row_data = bottom_row.find_all("td")
        try:
            mushrooms = tuple(map(int, bottom_row_data[0].text.split("-")))
            if len(mushrooms) != 7:
                mushrooms = None
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
            course, is200, date, time_, player, country, days, lap_times,
            coins, mushrooms, character, kart, tyres, glider, video_link)
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
        date, time_, video_link, player, country, days, lap_times, coins = (
            get_common_data(data))
        try:
            mushrooms = tuple(map(int, data[6 + lap_count].text.split("-")))
            if len(mushrooms) != 3:
                mushrooms = None
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
            course, is200, date, time_, player, country, days, lap_times,
            coins, mushrooms, character, kart, tyres, glider, video_link)
        records.append(record)
    return records


def main() -> None:
    """Main procedure of the scraper."""
    SNAPSHOT_FOLDER.mkdir(parents=True, exist_ok=True)
    records = []
    for course in COURSES:
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
    save_records(records)
    remove_old_snapshots()
    logging.info("Successfully saved all records to database.")


if __name__ == "__main__":
    logging.basicConfig(
        handlers=(
            logging.FileHandler(SCRAPE_LOG_FILE), logging.StreamHandler()),
        encoding="utf8", level=logging.INFO,
        format= "%(asctime)s: %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S")
    main()
