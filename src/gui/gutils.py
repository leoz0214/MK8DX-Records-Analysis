"""GUI-specific utilities (avoid module name clash with main utilities)."""
import pyglet

from const import LATO_FONT_FILE


pyglet.font.add_file(str(LATO_FONT_FILE))


def lato(size: int, bold: bool = False, italic: bool = False) -> tuple:
    """Utility function for the Lato font."""
    font = ("Lato", size)
    if bold:
        font += ("bold",)
    if italic:
        font += ("italic",)
    return font
