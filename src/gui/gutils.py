"""GUI-specific utilities (avoid module name clash with main utilities)."""
import datetime as dt
import tkinter as tk
from tkinter import messagebox
from tkinter import ttk
from typing import Callable

import matplotlib.dates as mdates
import pyglet
from tkcalendar import Calendar

from const import LATO_FONT_FILE


pyglet.font.add_file(str(LATO_FONT_FILE))
DEFAULT_RANK_TABLE_HEIGHT = 3
RANK_COL_WIDTH = 40
PLAYER_COL_WIDTH = 200
COUNTRY_COL_WIDTH = 200
BUILD_COL_WIDTH = 200
COUNT_COL_WIDTH = 100
PERCENTAGE_COL_WIDTH = 70
# Special quick dates that may be referenced.
SPECIAL_DATES = {
    dt.date(2023, 3, 8): "Day before Patch 1",
    dt.date(2023, 3, 9): "Day of Patch 1",
    dt.date(2023, 7, 11): "Day before Patch 2",
    dt.date(2023, 7, 12): "Day of Patch 2"
}



def lato(size: int, bold: bool = False, italic: bool = False) -> tuple:
    """Utility function for the Lato font."""
    font = ("Lato", size)
    if bold:
        font += ("bold",)
    if italic:
        font += ("italic",)
    return font


class RankTable(tk.Frame):
    """
    Convenient rank stat table which stores a fixed treeview
    determined at the point of creation. Can be used to store
    a table of data (top countries, top players etc...).
    """

    def __init__(
        self, master: tk.Widget,
        label: str, columns: tuple[str], rows: list[tuple],
        height: int = DEFAULT_RANK_TABLE_HEIGHT,
        column_widths: tuple[int] = None
    ) -> None:
        super().__init__(master)
        self.label = tk.Label(self, font=lato(15, True), text=label)
        columns = ("#", *columns)
        ttk.Style().configure("Treeview", rowheight=30)
        self.treeview = ttk.Treeview(
            self, columns=columns, show="headings", height=height)
        for column in columns:
            self.treeview.heading(column, text=column)
        if column_widths is not None:
            column_widths = (RANK_COL_WIDTH, *column_widths)
            for column, width in zip(columns, column_widths):
                self.treeview.column(column, width=width)
        for n, row in enumerate(rows, 1):
            row = (n, *row)
            self.treeview.insert("", "end", values=row)
        self.scrollbar = ttk.Scrollbar(
            self, orient="vertical", command=self.treeview.yview)
        self.treeview.config(yscrollcommand=self.scrollbar.set)
        self.label.grid(row=0, column=0, columnspan=2)
        self.treeview.grid(row=1, column=0)
        self.scrollbar.grid(row=1, column=1, sticky="ns")


class MillisecondsFormatter(mdates.DateFormatter):
    """
    Monkey patches the matplotlib date formatter to allow for milliseconds.
    Note: assumes last part of the string is indeed microseconds.
    Resolution of lap/finish times is indeed milliseconds only
    (no truncation issues).
    """

    def __call__(self, x, pos=0):
        """
        Monkey patched exactly from source except strips last 3 digits
        to show ms instead of us: may break in future... be warned!
        """
        result = mdates.num2date(x, self.tz).strftime(self.fmt)[:-3]
        return mdates._wrap_in_tex(result) if self._usetex else result


class DatePicker(tk.Toplevel):
    """Allows a date to be selected using the calendar."""

    def __init__(self, title: str, callback: Callable) -> None:
        super().__init__()
        self.title(title)
        self._initial_grab = self.grab_current()
        self.callback = callback
        self.protocol("WM_DELETE_WINDOW", self.close)
        self.grab_set()
        self.title_label = tk.Label(
            self, font=lato(25, True), text=title)
        self.calendar = Calendar(self)
        self.select_button = ttk.Button(
            self, text="Select", command=self.select)
        self.quick_dates_label = tk.Label(self, text="Quick dates:")

        self.title_label.pack(padx=10, pady=10)
        self.calendar.pack(padx=10, pady=10)
        self.select_button.pack(padx=10, pady=10)
        self.quick_dates_label.pack(padx=10, pady=10)

        for date, text in SPECIAL_DATES.items():
            quick_date_button = ttk.Button(
                self, text=f"{date} - {text}", width=30,
                command=self.select_quick_date(date))
            quick_date_button.pack(padx=10, pady=5)

    def select(self) -> None:
        """Selects the current date in the calendar."""
        self.close()
        self.callback(self.calendar._sel_date)
    
    def select_quick_date(self, date: dt.date) -> Calendar:
        """Wrapper for quick date selection."""
        def wrapper() -> None:
            self.close()
            self.callback(date)
        return wrapper

    def close(self) -> None:
        """Closes the date picker, returning control to master."""
        self.destroy()
        self._initial_grab.grab_set()


class DateRangeSelect(tk.Frame):
    """Allows the user to select a date range for analysis."""

    def __init__(self, master: tk.Widget) -> None:
        super().__init__(master)
        self.start_date = None
        self.end_date = None
        self.start_date_button = ttk.Button(
            self, text="Set Start Date",
            command=lambda: DatePicker("Set Start Date", self.set_start_date))
        self.end_date_button = ttk.Button(
            self, text="Set End Date",
            command=lambda: DatePicker("Set End Date", self.set_end_date))
        self.reset_start_date_button = ttk.Button(
            self, text="Reset Start Date",
            command=lambda: self.set_start_date(None))
        self.reset_end_date_button = ttk.Button(
            self, text="Reset End Date",
            command=lambda: self.set_end_date(None))
        self.label = tk.Label(self)
        self.update_label()
        self.label.grid(row=0, column=0, padx=5)
        self.start_date_button.grid(row=0, column=1, padx=5)
        self.end_date_button.grid(row=0, column=2, padx=5)
        self.reset_start_date_button.grid(row=0, column=3, padx=5)
        self.reset_end_date_button.grid(row=0, column=4, padx=5)
    
    def set_start_date(self, date: dt.date | None) -> None:
        """Sets the start date."""
        if (
            date is not None and self.end_date is not None
            and date > self.end_date
        ):
            messagebox.showerror(
                "Error", "Start date must not be later than end date.",
                parent=self)
            return
        self.start_date = date
        self.update_label()
    
    def set_end_date(self, date: dt.date | None) -> None:
        """Sets the end date."""
        if (
            date is not None and self.start_date is not None
            and date < self.start_date
        ):
            messagebox.showerror(
                "Error", "End date must not be earlier than start date.",
                parent=self)
            return
        self.end_date = date
        self.update_label()
    
    def update_label(self) -> None:
        """Updates the label based on start and end date."""
        if self.start_date is None and self.end_date is None:
            date_range = "All Time"
        elif self.start_date is None:
            date_range = f"Start - {self.end_date}"
        elif self.end_date is None:
            date_range = f"{self.start_date} - Current"
        else:
            date_range = f"{self.start_date} to {self.end_date}"
        self.label.config(text=f"Date Range: {date_range}")
