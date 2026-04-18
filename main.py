import flet as ft
from pickpic.ui.app import PickPicApp


def main(page: ft.Page):
    PickPicApp(page)


ft.app(target=main)
