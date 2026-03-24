import flet as ft

from views.home import HomeApp


async def main(page: ft.Page):
    page.title = "Coursera Downloader"
    page.window.resizable = False
    page.appbar = ft.AppBar(
        leading=ft.Icon(ft.Icons.MENU),
        title=page.title,
    )
    page.theme_mode = ft.ThemeMode.LIGHT
    home = HomeApp()
    page.add(
        ft.SafeArea(
            expand=True,
            content=ft.Container(
                padding=ft.Padding.symmetric(horizontal=10),
                content=home,
            ),
        )
    )


ft.run(main)
