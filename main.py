from pathlib import Path
import sys

import flet as ft

PROJECT_SRC = Path(__file__).resolve().parent / "src"
if str(PROJECT_SRC) not in sys.path:
    sys.path.insert(0, str(PROJECT_SRC))

from pickpic.ui.app import PickPicApp


def main(page: ft.Page):
    PickPicApp(page)


ft.app(target=main)