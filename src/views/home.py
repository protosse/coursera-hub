import flet as ft
from attrs import Factory

from config.constants import *
from utils.prefs import get_bool, set_bool


@ft.control
class HomeApp(ft.Column):
    isSpecial: bool = False

    def init(self):
        langs = list(ALL_Language.keys())
        self.special_check_box = ft.Checkbox(
            label="专项课程",
            value=False,
            on_change=self.handle_special_change,
        )
        self.controls = [
            ft.Row(
                [
                    TextFieldItem(title="课程链接（名字）"),
                    self.special_check_box,
                ],
            ),
            SelectItem(title="字幕1", items=langs),
            SelectItem(title="字幕2", items=langs, selected_index=1),
        ]

    def did_mount(self):
        self.page.run_task(self.updateSpecial)

    async def updateSpecial(self):
        is_special = await get_bool(PreferencesKeys.isSpecial, default=False)
        self.special_check_box.value = is_special
        self.update()

    async def handle_special_change(self, e: ft.Event[ft.Checkbox]):
        is_special = str(e.data).strip().lower() in {"1", "true", "t", "yes", "y", "on"}
        await set_bool(PreferencesKeys.isSpecial, is_special)


@ft.control
class TextFieldItem(ft.Row):
    title: str = ""

    def init(self):
        self.edit_view = ft.Ref[ft.TextField]()

        self.controls = [
            ft.Text(value=self.title),
            ft.TextField(ref=self.edit_view),
        ]


@ft.control
class SelectItem(ft.Row):
    title: str = ""
    items: list[str] = Factory(list)
    selected_index: int = 0

    def init(self):
        self.selected_text = ft.Ref[ft.Text]()
        picker = ft.CupertinoPicker(
            selected_index=self.selected_index,
            on_change=self.handle_selection_change,
            controls=[ft.Text(value=f) for f in self.items],
        )

        self.controls = [
            ft.Text(value=self.title),
            ft.TextButton(
                content=ft.Text(
                    value=self.items[self.selected_index],
                    ref=self.selected_text,
                ),
                style=ft.ButtonStyle(color=ft.Colors.BLUE),
                on_click=lambda e: self.page.show_dialog(
                    ft.CupertinoBottomSheet(
                        content=picker,
                        height=216,
                        padding=ft.Padding.only(top=6),
                    )
                ),
            ),
        ]

    def handle_selection_change(self, e: ft.Event[ft.CupertinoPicker]):
        self.selected_text.current.value = self.items[int(e.data)]
        self.update()
