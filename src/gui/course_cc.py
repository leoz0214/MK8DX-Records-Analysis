"""Data analysis for course/CC."""
import tkinter as tk
from collections import Counter
from tkinter import ttk

from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib import pyplot as plt

import main
from gutils import (
    lato, RankTable, COUNT_COL_WIDTH,  PLAYER_COL_WIDTH,
    COUNTRY_COL_WIDTH, BUILD_COL_WIDTH, PERCENTAGE_COL_WIDTH)
from utils import get_course_cc_records, ms_to_finish_time, Record


def sort_by_days_held(
    records: list[Record], uniques: set[str], field: str
) -> list[tuple]:
    """Returns records ranking days by player or country."""
    if not uniques:
        return []
    days_by = dict.fromkeys(uniques, 0)
    total_days = 0
    for record in records:
        days_by[getattr(record, field)] += record.days
        total_days += record.days
    # Sorts from most days held to least.
    days_by = dict(
        sorted(days_by.items(), key=lambda item: item[1], reverse=True))
    days_by_records = [
        (key, days, round(days / total_days * 100, 2))
        for key, days in days_by.items()]
    return days_by_records


def sort_by_records_count(records: list[Record], field: str) -> list[tuple]:
    """
    Returns records ranking number of records by player, country,
    character etc.
    """
    records_counts = Counter(getattr(record, field) for record in records)
    if None in records_counts:
        # Ignore empty values.
        records_counts.pop(None)
    if not records:
        # Somehow not a single record has the relevant data - no return.
        return []
    # Sorts from most records to least.
    records_counts = dict(
        sorted(records_counts.items(), key=lambda item: item[1], reverse=True))
    records_count_records = [
        (key, count, round(count / len(records) * 100, 2))
        for key, count in records_counts.items()]
    return records_count_records


class CourseCcAnalysis(tk.Frame):
    """Displays course/CC records insights and allows for data exporting."""

    def __init__(self, tab: main.Tab, course: str, is200: bool) -> None:
        super().__init__(tab)
        self.course = course
        self.is200 = is200
        self.records = get_course_cc_records(self.course, self.is200)
        self.unique_players = set(record.player for record in self.records)
        self.unique_countries = set(record.country for record in self.records)
        # Ignore 'None'
        unique_characters = set(
            record.character for record in self.records if record.character)
        unique_karts = set(
            record.kart for record in self.records if record.kart)
        unique_tyres = set(
            record.tyres for record in self.records if record.tyres)
        unique_gliders = set(
            record.glider for record in self.records if record.glider)

        self.title = tk.Label(
            self, font=lato(40, True),
            text=f"{self.course} {200 if self.is200 else 150}cc")
        self.current_records_frame = CurrentRecordsFrame(self)

        self.info_label = tk.Label(
            self, font=lato(15, italic=True), text=(
                f"Records: {len(self.records)} | "
                f"Players: {len(self.unique_players)} | "
                f"Countries: {len(self.unique_countries)} | "
                f"Characters: {len(unique_characters)} | "
                f"Karts: {len(unique_karts)} | "
                f"Tyres: {len(unique_tyres)} | "
                f"Gliders: {len(unique_gliders)}"))
        self.tables_frame = TablesFrame(self)
        self.graphs_button = ttk.Button(
            self, text="Open Graphs", command=self.open_graphs)
        self.export_button = ttk.Button(
            self, text="Export", command=self.export)

        self.title.pack(pady=5)
        self.current_records_frame.pack(pady=5)
        self.info_label.pack(pady=5)
        self.tables_frame.pack(pady=5)
        self.graphs_button.pack(pady=5)
        self.export_button.pack(pady=5)
    
    def open_graphs(self) -> None:
        """Opens the graphs toplevel to view graphs based on the stats."""
        GraphsToplevel(self)

    def export(self) -> None:
        """Allows exportation of the data to various file formats."""
        pass


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
                video_link_entry = ttk.Entry(self, width=48)
                video_link_entry.insert(0, record.video_link)
                video_link_entry.config(state="readonly")
                video_link_entry.pack()
        

class TablesFrame(tk.Frame):
    """Various tables providing various rank stats."""

    def __init__(self, master: CourseCcAnalysis) -> None:
        super().__init__(master)
        days_by_player_records = sort_by_days_held(
            master.records, master.unique_players, "player")
        self.days_by_player_frame = RankTable(
            self, "Days by Player", ("Player", "Days Held", "%"),
            days_by_player_records, column_widths=(
                PLAYER_COL_WIDTH, COUNT_COL_WIDTH, PERCENTAGE_COL_WIDTH))
        player_record_counts = sort_by_records_count(master.records, "player")
        self.player_records_counts_frame = RankTable(
            self, "Records by Player", ("Player", "Records", "%"),
            player_record_counts, column_widths=(
                PLAYER_COL_WIDTH, COUNT_COL_WIDTH, PERCENTAGE_COL_WIDTH))
        days_by_country_records = sort_by_days_held(
            master.records, master.unique_countries, "country")
        self.days_by_country_frame = RankTable(
            self, "Days by Country", ("Country", "Days Held", "%"),
           days_by_country_records, column_widths=(
                COUNTRY_COL_WIDTH, COUNT_COL_WIDTH, PERCENTAGE_COL_WIDTH))
        country_record_counts = (
            sort_by_records_count(master.records, "country"))
        self.country_records_counts_frame = RankTable(
            self, "Records by Country", ("Country", "Records", "%"),
            country_record_counts, column_widths=(
                COUNTRY_COL_WIDTH, COUNT_COL_WIDTH, PERCENTAGE_COL_WIDTH))

        character_record_counts = (
            sort_by_records_count(master.records, "character"))
        self.character_records_counts_frame = RankTable(
            self, "Records by Character", ("Character", "Records", "%"),
            character_record_counts, column_widths=(
                BUILD_COL_WIDTH, COUNT_COL_WIDTH, PERCENTAGE_COL_WIDTH))
        kart_record_counts = sort_by_records_count(master.records, "kart")
        self.kart_records_counts_frame = RankTable(
            self, "Records by Kart", ("Kart", "Records", "%"),
            kart_record_counts, column_widths=(
                BUILD_COL_WIDTH, COUNT_COL_WIDTH, PERCENTAGE_COL_WIDTH))
        tyres_record_counts = sort_by_records_count(master.records, "tyres")
        self.tyres_records_counts_frame = RankTable(
            self, "Records by Tyres", ("Tyres", "Records", "%"),
            tyres_record_counts, column_widths=(
                BUILD_COL_WIDTH, COUNT_COL_WIDTH, PERCENTAGE_COL_WIDTH))
        glider_record_counts = sort_by_records_count(master.records, "glider")
        self.glider_records_counts_frame = RankTable(
            self, "Records by Glider", ("Glider", "Records", "%"),
            glider_record_counts, column_widths=(
                BUILD_COL_WIDTH, COUNT_COL_WIDTH, PERCENTAGE_COL_WIDTH))
        self.days_by_player_frame.grid(row=0, column=0, padx=3, pady=3)
        self.player_records_counts_frame.grid(row=0, column=1, padx=3, pady=3)
        self.days_by_country_frame.grid(row=0, column=2, padx=3, pady=3)
        self.country_records_counts_frame.grid(row=0, column=3, padx=3, pady=3)
        self.character_records_counts_frame.grid(
            row=1, column=0, padx=3, pady=3)
        self.kart_records_counts_frame.grid(row=1, column=1, padx=3, pady=3)
        self.tyres_records_counts_frame.grid(row=1, column=2, padx=3, pady=3)
        self.glider_records_counts_frame.grid(row=1, column=3, padx=3, pady=3)


class GraphsToplevel(tk.Toplevel):
    """Display various graphs for a particular course/CC."""

    def __init__(self, master: CourseCcAnalysis) -> None:
        super().__init__()
        title = f"{master.course} {200 if master.is200 else 150}cc - Graphs"
        self.title(title)
        self.title_label = tk.Label(self, font=lato(25, True), text=title)

        import matplotlib.dates as mdates

        plt.figure()
        times = []
        dates = []
        for record in master.records:
            if record.date is not None:
                times.append(record.time)
                dates.append(record.date)
        plt.gca().xaxis.set_major_formatter(mdates.DateFormatter("%Y-%m-%d"))
        plt.gca().xaxis.set_major_locator(mdates.DayLocator())
        plt.gca().xaxis.set_major_locator(mdates.DayLocator(interval = 180))
        plt.plot(dates, times)
        plt.gcf().autofmt_xdate()
        figure = plt.gcf()
        graph = FigureCanvasTkAgg(figure, self)

        self.title_label.pack()
        graph.get_tk_widget().pack()
        