"""
Sends automated emails with information on
the new records from the previous snapshot.
"""
import datetime as dt
import json
import logging
import re
import smtplib
import time
from dataclasses import dataclass
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

import dominate
from dominate import tags
from dominate.util import text

import scrape
from const import EMAIL_CONFIG_FILE, EMAIL_LOG_FILE
from utils import (
    get_most_recent_snapshot, get_second_most_recent_snapshot,
    get_cc_records, Record, get_most_recent_snapshot_date_time,
    get_second_most_recent_snapshot_date_time, ms_to_finish_time)


@dataclass
class Config:
    """Settings for the email sending script."""
    sender: str
    password: str
    recipients: list[str]
    day_times: list[list[str]]


BASIC_EMAIL_REGEX = re.compile("^[^@]+@[^@]+\.[^@]+$")
DAYS_OF_WEEK = (
    "Monday", "Tuesday", "Wednesday", "Thursday", "Friday",
    "Saturday", "Sunday"
)
MAX_EMAIL_SEND_ATTEMPTS = 3
SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587


def valid_email(email: str) -> bool:
    """Returns True if a given email address is valid, else False."""
    return bool(BASIC_EMAIL_REGEX.match(email))


def valid_day_time(day_time: list[str]) -> bool:
    """Returns True if day of week and 24 hour time are valid."""
    day_of_week, time_= day_time
    if (
        day_of_week not in DAYS_OF_WEEK
        or not isinstance(time_, str)  or not len(time_) == 4
        or not time_.isdigit()
    ):
        return False
    hour, minute = int(time_[:2]), int(time_[2:])
    return 0 <= hour <= 23 and 0 <= minute <= 59


def get_config() -> Config:
    """Loads and validates the configuration settings."""
    with EMAIL_CONFIG_FILE.open("r", encoding="utf8") as f:
        config = json.load(f)
    sender = config["sender"]
    if not isinstance(sender, str):
        raise TypeError("Sender must be a string representing the email.")
    if not valid_email(sender):
        raise ValueError("Invalid sender email.")
    password = config["password"]
    if not isinstance(password, str):
        raise TypeError("Password must be a string.")
    recipients = config["recipients"]
    if not isinstance(recipients, list):
        raise TypeError(
            "Recipients must be a list of strings, even for 1 recipient.")
    if not recipients:
        raise ValueError("Recipients must not be empty.")
    if not all(isinstance(recipient, str) for recipient in recipients):
        raise TypeError(
            "Recipients must be all be strings representing the emails.")
    if not all(valid_email(recipient) for recipient in recipients):
        raise ValueError("Invalid recipient email detected.")
    day_times = config["day_times"]
    if not isinstance(day_times, list):
        raise TypeError(
            "Day/times must be a list of 2-tuples, "
            "even when only setting 1.")
    if not day_times:
        raise ValueError("Day times must not be empty.")
    if not all(
        isinstance(day_time, list) and len(day_time) == 2
        for day_time in day_times
    ):
        raise TypeError(
            "Day/times must all be length 2 in the form "
            "(day_of_week, 24_hour_time)")
    if not all(valid_day_time(day_time) for day_time in day_times):
        raise ValueError(
            "Day/times must all be length 2 in (day_of_week, 24_hour_time)\n"
            "Note: day of week must be Monday to Sunday (case-sensitive), "
            "24-hour time must be strictly in the format HHMM.")
    return Config(sender, password, recipients, day_times)


def get_new_records() -> list[tuple[Record, int]]:
    """
    Returns all new records between the
    previous snapshot and current snapshot.
    Returns Record objects paired with the milliseconds improvement.
    """
    previous_snapshot_path = get_second_most_recent_snapshot()
    current_snapshot_path = get_most_recent_snapshot()
    # Gets all 150/200cc records for previous and current snapshot.
    previous_records = (
        get_cc_records(False, database_path=previous_snapshot_path)
        + get_cc_records(True, database_path=previous_snapshot_path))
    current_records = (
        get_cc_records(False, database_path=current_snapshot_path)
        + get_cc_records(True, database_path=current_snapshot_path))
    previous_bests = {}
    current_bests = {}
    for records, dictionary in (
        (previous_records, previous_bests),
        (current_records, current_bests)
    ):
        for record in records:
            key = (record.course, record.is200)
            if key not in dictionary:
                dictionary[key] = record
                continue
            if record.time < dictionary[key].time:
                dictionary[key] = record
    new_records = [
        (record, previous_bests[key].time - record.time) 
            for key, record in current_bests.items()
                if record.time < previous_bests[key].time]
    return new_records


def generate_email() -> str:
    """Generates the HTML email and return the HTML document."""
    records = get_new_records()
    document = dominate.document(title="MK8DX Recent Records")
    with document.head:
        tags.style(
            r"""
            * {font-family: sans-serif;}
            #no-records {color: red;}
            """)
    with document:
        previous_date_time = (
            get_second_most_recent_snapshot_date_time().replace(microsecond=0))
        current_date_time = (
            get_most_recent_snapshot_date_time().replace(microsecond=0))
        with tags.p():
            tags.em(
                f"Date/Time Range: {previous_date_time} "
                f"-> {current_date_time}")
        if not records:
            tags.p(
                "There have not been any new world records "
                "within this time frame.", id="no-records")
        else:
            tags.p(
                f"{len(records)} course/CC combination"
                f"{'s have ' if len(records) > 1 else ' has '}"
                "had a new world record set within this time frame.")
            for record in records:
                record, improvement = record
                finish_time = ms_to_finish_time(record.time)
                lap_times = record.lap_times
                if lap_times is not None:
                    lap_times = tuple(
                        round(lap_time / 1000, 3) for lap_time in lap_times)
                tags.h1(f"{record.course} {200 if record.is200 else 150}cc")
                with tags.ul():
                    tags.li(f"Date: {record.date}")
                    tags.li(f"Time: {finish_time}")
                    tags.li(f"Player: {record.player}")
                    tags.li(f"Country: {record.country}")
                    tags.li(f"Improvement: {round(improvement / 1000, 3)}")
                    tags.li(f"Lap times: {lap_times}")
                    tags.li(f"Coins per lap: {record.coins}")
                    tags.li(f"Mushrooms per lap: {record.mushrooms}")
                    tags.li(f"Character: {record.character}")
                    tags.li(f"Kart: {record.kart}")
                    tags.li(f"Tyres: {record.tyres}")
                    tags.li(f"Glider: {record.glider}")
                    if record.video_link is not None:
                        with tags.li():
                            text(f"Video link: ")
                            tags.a(record.video_link, href=record.video_link)
                tags.hr()
    return document.render()


def send_email(config: Config, subject: str, body: str) -> None:
    """Sends the records report HTML email."""
    message = MIMEMultipart("alternative")
    message["Subject"] = subject
    message["From"] = config.sender
    # To avoid unnecessary email address leakage, 
    # recipients receive blind carbon copies.
    message["Bcc"] = ", ".join(config.recipients)
    message.attach(MIMEText(body, "html"))
    # Attempts email sending multiple times before giving up.
    attempts = MAX_EMAIL_SEND_ATTEMPTS
    while True:
        try:
            with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as smtp:
                smtp.ehlo()
                smtp.starttls()
                smtp.login(config.sender, config.password)
                smtp.send_message(message)
                return
        except Exception as e:
            attempts -= 1
            if not attempts:
                raise e
            time.sleep(1)


def main() -> None:
    """Main procedure of the email sender program."""
    try:
        get_most_recent_snapshot()
    except Exception:
        logging.error(
            "No initial snapshot - please run the scraper "
            "manually for the first snapshot.")
        return
    while True:
        config = get_config()
        date_time = dt.datetime.utcnow()
        time_string = (
            f"{str(date_time.hour).zfill(2)}{str(date_time.minute).zfill(2)}")
        for day_time in config.day_times:
            if (
                day_time[0] == DAYS_OF_WEEK[date_time.weekday()]
                and day_time[1] == time_string
            ):
                break
        else:
            # Not time yet.
            time.sleep(15)
            continue
        logging.info("Starting email generation.")
        scrape.main()
        email_content = generate_email()
        send_email(config, "MK8DX Recent Records", email_content)
        logging.info("Email update successfully sent to all recipients.")


if __name__ == "__main__":
    logging.basicConfig(
        handlers=(
            logging.FileHandler(EMAIL_LOG_FILE), logging.StreamHandler()),
        encoding="utf8", level=logging.INFO,
        format= "%(asctime)s: %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S")
    try:
        main()
    except Exception as e:
        logging.critical(f"Email script error: {e}")
