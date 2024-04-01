"""Data analysis for course/CC."""
import tkinter as tk

import main
from gutils import lato
from utils import get_course_cc_records, ms_to_finish_time


class CourseCcAnalysis(tk.Frame):
    """Displays course/CC records insights and allows for data exporting."""

    def __init__(self, tab: main.Tab, course: str, is200: bool) -> None:
        super().__init__(tab)
        self.records = get_course_cc_records(course, is200)
        self.title = tk.Label(
            self, font=lato(40, True),
            text=f"{course} {200 if is200 else 150}cc")
        self.current_records_frame = CurrentRecordsFrame(self)
        self.title.pack()
        self.current_records_frame.pack()


class CurrentRecordsFrame(tk.Frame):
    """Displays the current records (possibly ties)."""

    def __init__(self, master: CourseCcAnalysis) -> None:
        super().__init__(master)
        current_record_time = min(
            master.records, key=lambda record: record.time).time
        current_records = [
            record for record in master.records
                if record.time == current_record_time]
        self.label = tk.Label(
            self, font=lato(15, True),
            text=f"Current record{'s' if len(current_records) > 1 else ''}")
        self.label.pack()
        for record in current_records:
            finish_time = ms_to_finish_time(record.time)
            lap_times = record.lap_times
            if lap_times is not None:
                lap_times = tuple(round(lap / 1000, 3) for lap in lap_times)
            record_text = (
                f"Date: {record.date} | Time: {finish_time} | "
                f"Player: {record.player} | Country: {record.country} | "
                f"Days lasted: {record.days}\n"
                f"Lap times: {lap_times} | Coins per lap: {record.coins} | "
                f"Mushrooms per lap: {record.mushrooms}\n"
                f"Character: {record.character} | Kart: {record.kart} | "
                f"Tyres: {record.tyres} | Glider: {record.glider}")
            record_label = tk.Label(self, text=record_text)
            record_label.pack()
            if record.video_link is not None:
                video_link_entry = tk.Entry(self, width=32)
                video_link_entry.insert(0, record.video_link)
                video_link_entry.config(state="readonly")
                video_link_entry.pack()
