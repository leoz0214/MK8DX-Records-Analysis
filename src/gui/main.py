"""Main module for the GUI. This is where the GUI is launched from."""
import ctypes
import enum
import tkinter as tk
from tkinter import font
from tkinter import messagebox
from tkinter import ttk
from typing import Callable

# Very important line - DO NOT DELETE. Needed to access parent modules.
import __init__
import course_cc
from gutils import lato
from utils import get_courses, get_cups


TITLE = "MK8DX Records Analysis"
MAX_TABS = 10


class GeneralMode(enum.Enum):
    """Either 150cc only, 200cc only, or 150cc AND 200cc."""
    only150 = 0
    only200 = 1
    both = 2


class AnalysisGui(tk.Tk):
    """GUI window for data analysis features based on the world records."""

    def __init__(self) -> None:
        super().__init__()
        font.nametofont("TkDefaultFont").config(family="Lato", size=11)
        ttk.Style().configure("TNotebook.Tab", font=lato(15))
        self.title(TITLE)
        self.notebook_frame = tk.Frame(self, width=1800, height=900)
        self.notebook_frame.pack_propagate(False)
        self.notebook = ttk.Notebook(
            self.notebook_frame, width=1800, height=900)
        tabs = [Tab(self)]
        self.notebook.add(tabs[0], text="New")

        self.notebook.pack()
        self.notebook_frame.pack()


class Tab(tk.Frame):
    """
    Notebook tab that can be used to view analytics
    for both a single course/CC combo or general data.
    """

    def __init__(self, master: AnalysisGui) -> None:
        super().__init__(master)
        self.started = False

        self.label = tk.Label(self, font=lato(40, True), text="New Analysis")
        ttk.Style(self).configure("tab.TButton", font=lato(25))
        self.course_cc_button = ttk.Button(
            self, text="Course/CC", style="tab.TButton",
            command=self.prepare_course_cc_analysis)
        self.general_button = ttk.Button(
            self, text="General", style="tab.TButton",
            command=self.prepare_general_analysis)
        self.label.pack(padx=25, pady=25)
        self.course_cc_button.pack(padx=15, pady=15)
        self.general_button.pack(padx=15, pady=15)
    
    def start(self) -> None:
        """Registers start: destroys initial labels and buttons."""
        self.started = True
        self.label.destroy()
        self.course_cc_button.destroy()
        self.general_button.destroy()
    
    def prepare_course_cc_analysis(self) -> None:
        """Prepares analysis for a specific course/CC combination."""
        CourseCcSelectionToplevel(self.start_course_cc_analysis)
    
    def start_course_cc_analysis(
        self, toplevel: "CourseCcSelectionToplevel"
    ) -> None:
        """Starts course/CC analysis upon selecting course/CC."""
        self.start()
        try:
            course_cc.CourseCcAnalysis(
                self, toplevel.course, toplevel.is200).pack()
        except Exception as e:
            messagebox.showerror(
                "Error",
                    "Unfortunately, an error occurred "
                    f"while loading the course/CC analysis: {e}")
    
    def prepare_general_analysis(self) -> None:
        """Prepares general analysis for 150cc/200cc all courses."""
        GeneralSelectionToplevel(self.start_general_analysis)
    
    def start_general_analysis(
        self, toplevel: "GeneralSelectionToplevel"
    ) -> None:
        """Starts general analysis after 150cc, 200cc, or 150+200cc set."""
        self.start()
        self.started = True
        mode = toplevel.mode
        print(mode)
    

class CourseCcSelectionToplevel(tk.Toplevel):
    """Allows the user to select a course/CC pair."""

    def __init__(self, callback: Callable) -> None:
        super().__init__()
        self.title("Course/CC Selection")
        self.grab_set()
        self.callback = callback
        self.label = tk.Label(
            self, font=lato(40, True), text="Course/CC Selection")
        self.course_selection_frame = CourseSelectionFrame(self)
        self.cc_selection_frame = CcSelectionFrame(self)
        self.start_button = ttk.Button(self, text="Start", command=self.start)
        self.label.pack(pady=5)
        self.course_selection_frame.pack(pady=5)
        self.cc_selection_frame.pack(pady=5)
        self.start_button.pack(pady=5)
    
    def start(self) -> None:
        """Destroys window and calls the callback function."""
        self.destroy()
        self.callback(self)
    
    @property
    def course(self) -> str:
        return self.course_selection_frame.course
    
    @property
    def is200(self) -> bool:
        return self.cc_selection_frame.is200


class CourseSelectionFrame(tk.Frame):
    """Frame to select one of the 96 courses in the game."""

    def __init__(self, master: CourseCcSelectionToplevel) -> None:
        super().__init__(master)
        self._course = tk.StringVar(value="Mario Kart Stadium")
        courses = get_courses()
        cups = get_cups()
        for i, cup in enumerate(cups):
            cup_courses = courses[i*4:(i+1)*4]
            cup_courses_frame = CupCoursesFrame(self, cup, cup_courses)
            cup_courses_frame.grid(row=i//6, column=i%6, padx=5, pady=5)
    
    @property
    def course(self) -> str:
        return self._course.get()


class CupCoursesFrame(tk.Frame):
    """Frame containing the 4 courses of a particular cup."""

    def __init__(
        self, master: CourseSelectionFrame, cup: str, courses: list[str]
    ) -> None:
        super().__init__(master)
        self.label = tk.Label(self, font=lato(15, True), text=f"{cup} Cup")
        self.label.pack()
        ttk.Style(self).configure("course.TRadiobutton", font=lato(10))
        for course in courses:
            radiobutton = ttk.Radiobutton(
                self, text=course, value=course, style="course.TRadiobutton",
                variable=master._course, width=22)
            radiobutton.pack()


class CcSelectionFrame(tk.Frame):
    """Allows the user to select either 150cc or 200cc for course analysis."""

    def __init__(self, master: CourseCcSelectionToplevel) -> None:
        super().__init__(master)
        self._is200 = tk.BooleanVar(value=False)
        ttk.Style(self).configure("cc.TRadiobutton", font=lato(25))
        self._150cc = ttk.Radiobutton(
            self, text="150cc", value=False,
            variable=self._is200, style="cc.TRadiobutton", width=5)
        self._200cc = ttk.Radiobutton(
            self, text="200cc", value=True,
            variable=self._is200, style="cc.TRadiobutton", width=5)
        self._150cc.pack(side="left", padx=10)
        self._200cc.pack(side="right", padx=10)
    
    @property
    def is200(self) -> bool:
        return self._is200.get()
    

class GeneralSelectionToplevel(tk.Toplevel):
    """Allows the user to select 150cc/200cc only, or 150cc and 200cc."""

    def __init__(self, callback: Callable) -> None:
        super().__init__()
        self.title("General Mode Selection")
        self.grab_set()
        self.callback = callback
        self._mode = tk.IntVar(value=GeneralMode.only150.value)
        self.label = tk.Label(
            self, font=lato(40, True), text="General Mode Selection")
        self.label.pack(pady=10)
        ttk.Style(self).configure("mode.TRadiobutton", font=lato(25))
        for i, text in enumerate(
            ("150cc only", "200cc only", "Both 150cc and 200cc")
        ):
            radiobutton = ttk.Radiobutton(
                self, text=text, value=i,
                variable=self._mode, width=20, style="mode.TRadiobutton")
            radiobutton.pack(pady=5)
        self.start_button = ttk.Button(self, text="Start", command=self.start)
        self.start_button.pack(pady=5)
    
    def start(self) -> None:
        """Destroys window and calls the callback function."""
        self.destroy()
        self.callback(self)
    
    @property
    def mode(self) -> GeneralMode:
        return GeneralMode(self._mode.get())


def main() -> None:
    """Main procedure of the program."""
    ctypes.windll.shcore.SetProcessDpiAwareness(True)
    AnalysisGui().mainloop()


if __name__ == "__main__":
    main()
