import asyncio
import logging
from dataclasses import dataclass, field

import flet as ft

from config.constants import *
from coursera_dl.coursera_dl import main_f as m
from utils.prefs import get_str, set_str


class FletLogHandler(logging.Handler):
    """自定义日志处理器，将日志输出到 Flet 的 ListView"""

    def __init__(self, state):
        super().__init__()
        self.state = state

    def emit(self, record):
        """处理日志记录"""
        msg = self.format(record)
        self._add_log(msg)

    def _add_log(self, message):
        """添加日志到 ListView"""
        messages = self.state.messages
        messages.append(message)
        if len(messages) > 1000:
            messages = messages[-1000:]
        self.state.messages = messages


@ft.observable
@dataclass
class HomeState:
    lang1: str = ""
    lang2: str = ""
    browser: str = ""
    download_dir: str = ""
    messages: list[str] = field(default_factory=list)

    async def load_state(self):
        lang1 = await get_str(PreferencesKeys.lang1, default="英文")
        lang2 = await get_str(PreferencesKeys.lang2, default="中文")
        browser = await get_str(PreferencesKeys.browser, default="edge")
        download_dir = await get_str(PreferencesKeys.download_dir, default="请选择")

        self.lang1 = lang1
        self.lang2 = lang2
        self.browser = browser
        self.download_dir = download_dir

    async def set_lang1(self, value: str):
        self.lang1 = value
        await set_str(PreferencesKeys.lang1, value)

    async def set_lang2(self, value: str):
        self.lang2 = value
        await set_str(PreferencesKeys.lang2, value)

    async def set_browser(self, value: str):
        self.browser = value
        await set_str(PreferencesKeys.browser, value)

    async def set_download_dir(self, value: str):
        self.download_dir = value
        await set_str(PreferencesKeys.download_dir, value)


@ft.component
def HomeView():
    state, _ = ft.use_state(HomeState())

    def on_mount():
        asyncio.create_task(state.load_state())

    # 只在首次加载时执行
    ft.use_effect(on_mount, [])

    # 设置日志处理器
    root_logger = logging.getLogger()
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)
    handler = FletLogHandler(state)
    root_logger.addHandler(handler)
    root_logger.setLevel(logging.INFO)

    langs = list(ALL_Language.keys())
    browsers = list(ALL_BROWERS.keys())

    course_url = ft.Ref[ft.TextField]()
    is_special = ft.Ref[ft.Checkbox]()

    async def download_dir_pick_clicked(e: ft.Event[ft.Button]):
        path = await ft.FilePicker().get_directory_path()
        if path:
            await state.set_download_dir(path)

    def download_clicked(e: ft.Event[ft.Button]):
        cmd = [
            "--specialization",
            "fashion-silhouettes-icons",
            "--download-quizzes",
            "--download-notebooks",
            "--disable-url-skipping",
            "--unrestricted-filenames",
            "--combined-section-lectures-nums",
            "--jobs",
            "2",
            "--cauth",
            "52Mqyz756nKYLElgoEPJj_gBpJbw7qvGiGmE9MAWTtI7_l05neIiQ8YV_YolGK1nmst0y0llQKPB44hkESmgCA.sCYMGYnqMllqkHTXrFvd-Q._hFqNImgwGFzUenS3YssEiV98ZiuoUW-muTnd9GbD8uJ2LqUPLX-8ADdu929VDjPFYsaFfdW1a1XgXZPvyF7HeXxSUeoX7Ml1If9EdC1PAqzDTG9mdQmftGhP6Q9VaWFlXIOsA0FU9ZTc98nu7L6Bl7k_C-RUFxj7HQ0JAbyGqH90le065HydJ_HE2S75NQIC4c6l-mtb_2m8ABZaDJe467ZRZQF1cC-iJ65JEwIff2_LHEDZ6X-z9Mg4N9y6YCeTqDbOc4LcL3_10fyaUa2WKgueJPsfbS9TrtVh64Aobkb1HJ6qKH3MrVCDwpSibXADNDatVxEKbUcRh2D-is8ewk6LDT8uQKfirmPeVEM6314KM9voP51JhIMPAsPWpuEMzotjLaRrzgDZCGBESf6eN2ORMOjb6E1kwhAx3T769MSL4xIMI1LJ-7j889lgDH9sf2o5z3BhIzwmXOD14T9F6HFek7F3WBF6cd0OEYB3Ho",
            "--subtitle-language",
            "en,zh-CN|zh-TW",
            "--video-resolution",
            "720p",
            "--download-delay",
            "10",
            "--cache-syllabus",
            "--aria2",
        ]

        try:
            m(cmd)
        except Exception as e:
            pass

    print("render HomeView")
    return ft.Column(
        controls=[
            ft.DropdownM2(
                label="浏览器",
                value=state.browser,
                options=[ft.dropdownm2.Option(key=v, text=v) for v in browsers],
                on_change=lambda e: asyncio.create_task(state.set_browser(e.data)),
            ),
            ft.Row(
                controls=[
                    ft.TextField(
                        label="课程链接（名字）",
                        ref=course_url,
                    ),
                    ft.Checkbox(
                        label="专项课程",
                        ref=is_special,
                    ),
                ]
            ),
            ft.Row(
                controls=[
                    ft.DropdownM2(
                        label="字幕1",
                        value=state.lang1,
                        options=[ft.dropdownm2.Option(key=v, text=v) for v in langs],
                        on_change=lambda e: asyncio.create_task(
                            state.set_lang1(e.data)
                        ),
                    ),
                    ft.DropdownM2(
                        label="字幕2",
                        value=state.lang2,
                        options=[ft.dropdownm2.Option(key=v, text=v) for v in langs],
                        on_change=lambda e: asyncio.create_task(
                            state.set_lang2(e.data)
                        ),
                    ),
                ]
            ),
            ft.Row(
                controls=[
                    ft.TextField(
                        label="下载目录", value=state.download_dir, expand=True
                    ),
                    ft.Button(
                        content="选择", on_click=download_dir_pick_clicked, width=80
                    ),
                ],
                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
            ),
            ft.Row(
                controls=[
                    ft.Container(
                        expand=True,
                    ),
                    ft.Button("下载", on_click=download_clicked),
                    ft.Button("继续"),
                ]
            ),
            ft.Container(
                content=ft.ListView(
                    expand=True,
                    spacing=5,
                    padding=10,
                    auto_scroll=True,
                    controls=[ft.Text(m) for m in state.messages],
                ),
                border=ft.border.all(1, ft.Colors.GREY_300),
                border_radius=5,
                expand=True,
            ),
        ]
    )
