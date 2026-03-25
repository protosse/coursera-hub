import flet as ft

from views.home import HomeView


@ft.component
def App():
    return ft.SafeArea(
        expand=True,
        content=ft.Container(
            padding=ft.Padding.symmetric(horizontal=10),
            content=HomeView(),
        ),
    )


def main(page: ft.Page):
    page.title = "Coursera Downloader"
    page.window.resizable = False
    page.appbar = ft.AppBar(
        leading=ft.Icon(ft.Icons.MENU),
        title=page.title,
    )
    page.theme_mode = ft.ThemeMode.LIGHT
    page.render(App)


ft.run(main)
