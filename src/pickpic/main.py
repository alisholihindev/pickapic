import flet as ft
from pickpic.ui.app import PickPicApp


def _app(page: ft.Page):
    PickPicApp(page)


def main():
    ft.app(target=_app)


if __name__ == "__main__":
    main()
