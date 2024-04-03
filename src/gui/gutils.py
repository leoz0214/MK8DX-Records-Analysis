"""GUI-specific utilities (avoid module name clash with main utilities)."""
import tkinter as tk
from tkinter import ttk

import matplotlib.dates as mdates
import pyglet

from const import LATO_FONT_FILE


pyglet.font.add_file(str(LATO_FONT_FILE))
DEFAULT_RANK_TABLE_HEIGHT = 3
RANK_COL_WIDTH = 40
PLAYER_COL_WIDTH = 200
COUNTRY_COL_WIDTH = 200
BUILD_COL_WIDTH = 200
COUNT_COL_WIDTH = 100
PERCENTAGE_COL_WIDTH = 70


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
