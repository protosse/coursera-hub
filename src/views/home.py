import asyncio
import logging
import platform
from dataclasses import dataclass, field

import flet as ft

from config.constants import *
from coursera_dl.coursera_dl import main_f as m
from utils.prefs import get_bool, get_str, set_bool, set_str


@ft.observable
@dataclass
class HomeState:
    is_special: bool = False
    cauth_cookie: str = ""
    course_url: str = ""
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
        course_url = await get_str(PreferencesKeys.course_url, default="")
        is_special = await get_bool(PreferencesKeys.is_special, default=False)
        cauth_cookie = await get_str(PreferencesKeys.cauth_cookie, default="")

        self.is_special = is_special
        self.cauth_cookie = cauth_cookie
        self.course_url = course_url
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

    async def set_course_url(self, value: str):
        self.course_url = value
        await set_str(PreferencesKeys.course_url, value)

    async def set_is_special(self, value: bool):
        self.is_special = value
        await set_bool(PreferencesKeys.is_special, value)

    async def set_cauth_cookie(self, value: str):
        self.cauth_cookie = value
        await set_str(PreferencesKeys.cauth_cookie, value)


class FletLogHandler(logging.Handler):
    def __init__(self, state: HomeState):
        super().__init__()
        self.state = state

    def emit(self, record):
        msg = self.format(record)
        self._add_log(msg)

    def _add_log(self, message):
        pass
        # print(message)
        # messages = self.state.messages
        # messages.append(message)
        # if len(messages) > 1000:
        #     messages = messages[-1000:]
        # self.state.messages = messages.copy()


@ft.component
def HomeView():
    state, _ = ft.use_state(HomeState())

    def on_mount():
        asyncio.create_task(state.load_state())
        # 设置日志处理器
        root_logger = logging.getLogger()
        for handler in root_logger.handlers[:]:
            root_logger.removeHandler(handler)
        handler = FletLogHandler(state)
        root_logger.addHandler(handler)
        root_logger.setLevel(logging.INFO)

    # 只在首次加载时执行
    ft.use_effect(on_mount, [])

    langs = list(ALL_Language.keys())
    browsers = list(ALL_BROWERS.keys())
    is_mac = platform.system() == "Darwin"

    async def download_dir_pick_clicked(e: ft.Event[ft.Button]):
        path = await ft.FilePicker().get_directory_path()
        if path:
            await state.set_download_dir(path)

    def download_clicked(e: ft.Event[ft.Button]):
        run_command(False)

    def resume_clicked(e: ft.Event[ft.Button]):
        run_command(True)

    def run_command(resume: bool):
        if len(state.course_url) == 0:
            logging.info("请输入课程链接或名称")
            return
        cmd = []
        if state.is_special:
            cmd.append("--specialization")
        cmd.append(state.course_url)
        cmd.append("--download-quizzes")
        cmd.append("--download-notebooks")
        cmd.append("--disable-url-skipping")
        cmd.append("--unrestricted-filenames")
        cmd.append("--combined-section-lectures-nums")
        cmd.append("--jobs")
        cmd.append("2")
        cmd.append("--video-resolution")
        cmd.append("720p")
        cmd.append("--download-delay")
        cmd.append("10")

        all_langs = [ALL_Language[v] for v in langs]
        cmd.append("--subtitle-language")
        cmd.append(",".join(all_langs))

        if is_mac:
            cmd.append("--cauth")
            cmd.append(state.cauth_cookie)
        else:
            cmd.append("--cauth-auto")
            cmd.append(state.browser)
        cmd.append("--path")
        cmd.append(state.download_dir)
        if resume:
            cmd.append("--resume")
        cmd.append("--cache-syllabus")

        try:
            m(cmd)
        except Exception as e:
            logging.error(f"发生错误：{e}")

    @ft.component
    def cookie_view():
        if is_mac:
            return ft.Row(
                controls=[
                    ft.TextField(
                        label="CAUTH",
                        expand=True,
                        value=state.cauth_cookie,
                        on_change=lambda e: asyncio.create_task(
                            state.set_cauth_cookie(e.data)
                        ),
                    )
                ]
            )
        else:
            return (
                ft.DropdownM2(
                    label="浏览器",
                    value=state.browser,
                    options=[ft.dropdownm2.Option(key=v, text=v) for v in browsers],
                    on_change=lambda e: asyncio.create_task(state.set_browser(e.data)),
                ),
            )

    return ft.Column(
        controls=[
            cookie_view(),
            ft.Row(
                controls=[
                    ft.TextField(
                        label="课程链接（名字）",
                        value=state.course_url,
                        on_change=lambda e: asyncio.create_task(
                            state.set_course_url(e.data)
                        ),
                    ),
                    ft.Checkbox(
                        label="专项课程",
                        value=state.is_special,
                        on_change=lambda e: asyncio.create_task(
                            state.set_is_special(e.data)
                        ),
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
                    ft.Button("继续", on_click=resume_clicked),
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
