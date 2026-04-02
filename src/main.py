import json
import logging
from pathlib import Path

import flet as ft
from flet import Border

from constants import *
from coursera_helper_wrapper import CourseraHelperWrapper


class CourseraHub:
    def __init__(self, page: ft.Page):
        self.page = page
        self.page.title = "Coursera Hub"
        self.page.window.resizable = False
        self.page.theme_mode = ft.ThemeMode.LIGHT

        # 创建coursera-helper实例
        self.coursera_helper = CourseraHelperWrapper()

        # 配置文件路径
        self.config_path = Path.home() / ".coursera_hub_config.json"

        self.langs = list(Language)
        self.browsers = list(Browser)
        self.download_tools = list(DownloadTool)

        # 全局变量
        self.auth_method = AuthMethod.CAUTH
        self.cauth = ""
        self.username = ""
        self.password = ""
        self.course_name = ""
        self.download_path = str(Path.home())
        self.subtitle_language1 = Language.ENGLISH
        self.subtitle_language2 = Language.CHINESE
        self.is_special = False
        self.browser = Browser.EDGE
        self.download_tool = DownloadTool.default

        # 创建输出日志控件的ref
        self.output_list_view = ft.Ref[ft.ListView]()
        self.auth_details = ft.Row()
        self.download_path_field = ft.Ref[ft.TextField]()

        # 创建消息队列用于线程间通信
        import queue

        self.message_queue = queue.Queue()

        # 下载线程和取消标志
        self.download_thread = None
        self.list_thread = None
        self.cancel_download = False

        # 加载配置
        self.load_config()

        # 创建UI
        self.create_ui()

        # 配置日志捕获
        self.setup_logging()

    def create_ui(self):
        # 创建页面布局，直接添加到页面
        self.page.add(
            # 认证方式
            ft.Container(
                content=ft.Column(
                    controls=[
                        ft.RadioGroup(
                            value=self.auth_method.value,
                            on_change=self.auth_method_changed,
                            content=ft.Row(
                                controls=[
                                    ft.Radio(
                                        label="CAUTH",
                                        value=AuthMethod.CAUTH.value,
                                    ),
                                    ft.Radio(
                                        label="浏览器Cookie",
                                        value=AuthMethod.BROWSER.value,
                                    ),
                                    ft.Radio(
                                        label="用户名密码",
                                        value=AuthMethod.CREDENTIALS.value,
                                    ),
                                ]
                            ),
                        ),
                        self.auth_details,
                    ]
                ),
                padding=10,
                border=Border.all(1, ft.Colors.GREY_300),
                border_radius=8,
                margin=ft.Margin(bottom=10),
            ),
            ft.Row(
                controls=[
                    ft.TextField(
                        label="课程名称",
                        hint_text="请输入课程名称",
                        value=self.course_name,
                        on_change=self.course_name_changed,
                        expand=True,
                    ),
                    ft.Checkbox(
                        label="专项课程",
                        value=self.is_special,
                        on_change=self.is_special_changed,
                    ),
                    ft.DropdownM2(
                        label="下载工具",
                        value=self.download_tool.value,
                        options=[
                            ft.dropdownm2.Option(key=v.value, text=v.value)
                            for v in self.download_tools
                        ],
                        on_change=self.download_tool_changed,
                    ),
                ]
            ),
            ft.Row(
                controls=[
                    ft.TextField(
                        ref=self.download_path_field,
                        label="下载路径",
                        value=self.download_path,
                        expand=True,
                        on_change=self.download_path_changed,
                    ),
                    ft.Button("浏览", on_click=self.browse_path),
                ],
                spacing=10,
            ),
            ft.Row(
                controls=[
                    ft.DropdownM2(
                        label="字幕1",
                        value=self.subtitle_language1.value,
                        options=[
                            ft.dropdownm2.Option(key=v.value, text=v.value)
                            for v in self.langs
                        ],
                        on_change=self.subtitle_language1_changed,
                    ),
                    ft.DropdownM2(
                        label="字幕2",
                        value=self.subtitle_language2.value,
                        options=[
                            ft.dropdownm2.Option(key=v.value, text=v.value)
                            for v in self.langs
                        ],
                        on_change=self.subtitle_language2_changed,
                    ),
                ]
            ),
            # 操作按钮
            ft.Row(
                controls=[
                    ft.Button("列出课程", on_click=self.list_courses),
                    ft.Button(
                        "下载课程",
                        on_click=self.download_course,
                        bgcolor=ft.Colors.BLUE,
                        color=ft.Colors.WHITE,
                    ),
                    ft.Button(
                        "恢复下载",
                        on_click=self.resume_download,
                        bgcolor=ft.Colors.BLUE,
                        color=ft.Colors.WHITE,
                    ),
                    ft.Button(
                        "取消下载",
                        on_click=self.cancel_download_click,
                        bgcolor=ft.Colors.RED,
                        color=ft.Colors.WHITE,
                    ),
                    ft.Button("清空日志", on_click=self.clear_log),
                ],
                spacing=10,
                alignment=ft.MainAxisAlignment.CENTER,
            ),
            # 输出日志
            ft.Container(
                content=ft.ListView(
                    controls=[],
                    ref=self.output_list_view,
                    auto_scroll=True,
                    expand=True,
                ),
                padding=10,
                border=Border.all(1, ft.Colors.GREY_300),
                border_radius=8,
                margin=ft.Margin(top=10),
                expand=True,
            ),
        )

        # 更新认证详情
        self.update_auth_details()

    def auth_method_changed(self, e):
        self.auth_method = AuthMethod(e.control.value)
        self.update_auth_details()
        self.save_config()

    def update_auth_details(self):
        self.auth_details.controls.clear()

        if self.auth_method == AuthMethod.CAUTH:
            self.auth_details.controls.append(
                ft.TextField(
                    label="CAUTH值",
                    hint_text="输入CAUTH值",
                    value=self.cauth,
                    on_change=self.cauth_changed,
                )
            )
        elif self.auth_method == AuthMethod.CREDENTIALS:
            self.auth_details.controls.append(
                ft.TextField(
                    label="用户名/邮箱",
                    hint_text="输入用户名或邮箱",
                    value=self.username,
                    on_change=self.username_changed,
                )
            )
            self.auth_details.controls.append(
                ft.TextField(
                    label="密码",
                    hint_text="输入密码",
                    value=self.password,
                    on_change=self.password_changed,
                )
            )
        elif self.auth_method == AuthMethod.BROWSER:
            self.auth_details.controls.append(
                ft.DropdownM2(
                    label="浏览器",
                    value=self.browser.value,
                    options=[
                        ft.dropdownm2.Option(key=v.value, text=v.value)
                        for v in self.browsers
                    ],
                    on_change=self.browser_change,
                )
            )

        self.auth_details.update()

    def cauth_changed(self, e):
        self.cauth = e.control.value
        self.save_config()

    def username_changed(self, e):
        self.username = e.control.value
        self.save_config()

    def password_changed(self, e):
        self.password = e.control.value
        self.save_config()

    def course_name_changed(self, e):
        self.course_name = e.control.value
        self.save_config()

    def download_path_changed(self, e):
        self.download_path = e.control.value
        self.save_config()

    async def browse_path(self, e):
        path = await ft.FilePicker().get_directory_path()
        if path:
            self.download_path_field.current.value = path
            self.page.update()
            self.download_path = path
            self.save_config()

    def is_special_changed(self, e):
        self.is_special = e.control.value
        self.save_config()

    def download_tool_changed(self, e):
        self.download_tool = DownloadTool(e.control.value)
        self.save_config()

    def browser_change(self, e):
        self.browser = Browser(e.control.value)
        self.save_config()

    def subtitle_language1_changed(self, e):
        self.subtitle_language1 = Language(e.control.value)
        self.save_config()

    def subtitle_language2_changed(self, e):
        self.subtitle_language2 = Language(e.control.value)
        self.save_config()

    async def list_courses(self, e):
        def run_list_courses():
            self.message_queue.put("正在列出课程...")

            # 先进行认证
            if self.auth_method == AuthMethod.CAUTH and self.cauth:
                success, message = self.coursera_helper.authenticate(
                    AuthMethod.CAUTH, cauth=self.cauth
                )
                self.message_queue.put(message)
                if not success:
                    return
            elif (
                self.auth_method == AuthMethod.CREDENTIALS
                and self.username
                and self.password
            ):
                success, message = self.coursera_helper.authenticate(
                    AuthMethod.CREDENTIALS,
                    username=self.username,
                    password=self.password,
                )
                self.message_queue.put(message)
                if not success:
                    return
            elif self.auth_method == AuthMethod.BROWSER:
                success, message = self.coursera_helper.authenticate(AuthMethod.BROWSER)
                self.message_queue.put(message)
                if not success:
                    return
            else:
                self.message_queue.put("错误：请输入完整的认证信息")
                return

            # 调用coursera-helper的list_courses方法
            courses = self.coursera_helper.list_courses()

            if isinstance(courses, list):
                self.message_queue.put("列出课程成功！")
                for course in courses:
                    self.message_queue.put(course)
            else:
                self.message_queue.put(f"列出课程失败: {courses}")

        import threading

        self.list_thread = threading.Thread(target=run_list_courses, daemon=True)
        self.list_thread.start()

        await self.process_message_queue()

    async def download_course(self, e):
        await self.download(resume=False)

    async def resume_download(self, e):
        await self.download(resume=True)

    async def download(self, resume: bool = False):
        if not self.course_name:
            self.append_output("错误：请输入课程名称")
            return

        # 在后台线程中运行下载，避免阻塞UI
        import threading

        def run_download():
            # 先进行认证
            if self.auth_method == AuthMethod.CAUTH and self.cauth:
                success, message = self.coursera_helper.authenticate(
                    AuthMethod.CAUTH, cauth=self.cauth
                )
                # 将消息放入队列
                self.message_queue.put(message)
                if not success:
                    return
            elif (
                self.auth_method == AuthMethod.CREDENTIALS
                and self.username
                and self.password
            ):
                success, message = self.coursera_helper.authenticate(
                    AuthMethod.CREDENTIALS,
                    username=self.username,
                    password=self.password,
                )
                self.message_queue.put(message)
                if not success:
                    return
            elif self.auth_method == AuthMethod.BROWSER:
                success, message = self.coursera_helper.authenticate(AuthMethod.BROWSER)
                self.message_queue.put(message)
                if not success:
                    return
            else:
                self.message_queue.put("错误：请输入完整的认证信息")
                return

            # 调用coursera-helper的download_course方法
            langs = [
                v.code for v in set([self.subtitle_language1, self.subtitle_language2])
            ]
            download_options = {
                "subtitle_language": ",".join(langs),
                "video_resolution": "720p",
                "download_quizzes": True,
                "download_notebooks": True,
                "specialization": self.is_special,
            }

            match self.download_tool:
                case DownloadTool.default:
                    pass
                case _:
                    download_options[self.download_tool.name] = self.download_tool.value

            if resume:
                download_options["resume"] = True
                download_options["cache_syllabus"] = True

            # 使用生成器实时显示下载进度
            for progress_message in self.coursera_helper.download_course(
                self.course_name,
                self.download_path,
                lambda: self.cancel_download,
                **download_options,
            ):
                # 检查是否取消
                if self.cancel_download:
                    self.message_queue.put("下载已取消")
                    break
                self.message_queue.put(progress_message)

        # 重置取消标志
        self.cancel_download = False

        # 启动后台线程
        self.download_thread = threading.Thread(target=run_download, daemon=True)
        self.download_thread.start()

        # 启动消息处理循环
        await self.process_message_queue()

    def cancel_download_click(self, e):
        """取消下载"""
        if self.download_thread and self.download_thread.is_alive():
            self.cancel_download = True
            self.append_output("正在取消下载...")
        else:
            self.append_output("没有正在进行的下载任务")

    def clear_log(self, e):
        """清空日志"""
        if self.output_list_view.current:
            self.output_list_view.current.controls.clear()
            self.page.update()

    async def process_message_queue(self):
        """处理消息队列中的消息"""
        import asyncio

        while True:
            try:
                while not self.message_queue.empty():
                    message = self.message_queue.get(block=False)
                    self.append_output(message)
                    self.message_queue.task_done()
            except:
                pass

            has_active_thread = (
                self.download_thread and self.download_thread.is_alive()
            ) or (self.list_thread and self.list_thread.is_alive())

            if has_active_thread or not self.message_queue.empty():
                await asyncio.sleep(0.1)
            else:
                break

    def append_output(self, text):
        # 使用ref直接获取ListView控件
        if self.output_list_view.current:
            # 检查是否是进度条信息（以\r开头）
            if text.startswith("\r") or text.startswith("#"):
                # 移除\r并更新最后一个文本控件
                text = text[1:]
                if self.output_list_view.current.controls:
                    # 更新最后一个控件
                    last_control = self.output_list_view.current.controls[-1]
                    if isinstance(last_control, ft.Text):
                        last_control.value = text
                    else:
                        # 如果最后一个不是Text控件，添加新的
                        self.output_list_view.current.controls.append(
                            ft.Text(text, selectable=True)
                        )
                else:
                    # 如果没有控件，添加新的
                    self.output_list_view.current.controls.append(
                        ft.Text(text, selectable=True)
                    )
            else:
                # 添加新的日志条目
                self.output_list_view.current.controls.append(
                    ft.Text(text, selectable=True)
                )
            # 更新UI
            self.output_list_view.current.update()
            self.page.update()

    def setup_logging(self):
        """配置日志捕获"""

        # 创建自定义日志处理器
        class UILogHandler(logging.Handler):
            def __init__(self, app):
                super().__init__()
                self.app = app
                self.setFormatter(logging.Formatter("%(message)s"))

            def emit(self, record):
                msg = self.format(record)
                self.app.append_output(msg)

        # 获取root logger
        root_logger = logging.getLogger()
        root_logger.setLevel(logging.INFO)

        # 添加UI日志处理器
        ui_handler = UILogHandler(self)
        root_logger.addHandler(ui_handler)

        # 保存原始的print函数
        import builtins

        self.original_print = builtins.print

        # 捕获print输出，但避免无限递归
        def custom_print(*args, **kwargs):
            # 将输出发送到原始print
            self.original_print(*args, **kwargs)
            # 将输出发送到UI，但避免递归
            import traceback

            stack = traceback.extract_stack()
            # 检查调用栈，避免处理append_output内部的调用
            for frame in stack:
                if frame.name == "append_output":
                    return
            text = " ".join(str(arg) for arg in args)
            self.append_output(text)

        # 替换全局print函数
        builtins.print = custom_print

    def load_config(self):
        """加载配置"""
        if self.config_path.exists():
            try:
                with open(self.config_path, "r", encoding="utf-8") as f:
                    config = json.load(f)
                    self.auth_method = AuthMethod(
                        config.get("auth_method", AuthMethod.CAUTH.value)
                    )
                    self.cauth = config.get("cauth", "")
                    self.username = config.get("username", "")
                    self.password = config.get("password", "")
                    self.course_name = config.get("course_name", "")
                    self.download_path = config.get("download_path", str(Path.home()))
                    self.subtitle_language1 = Language(
                        config.get("subtitle_language1", self.langs[0].value)
                    )
                    self.subtitle_language2 = Language(
                        config.get("subtitle_language2", self.langs[1].value)
                    )
                    self.is_special = config.get("is_special", False)
                    self.browser = Browser(config.get("browser", Browser.EDGE.value))
                    self.download_tool = DownloadTool(
                        config.get("download_tool", DownloadTool.default.value)
                    )
            except Exception as e:
                print(f"加载配置失败: {e}")

    def save_config(self):
        """保存配置"""
        config = {
            "auth_method": self.auth_method.value,
            "cauth": self.cauth,
            "username": self.username,
            "password": self.password,
            "course_name": self.course_name,
            "download_path": self.download_path,
            "subtitle_language1": self.subtitle_language1.value,
            "subtitle_language2": self.subtitle_language2.value,
            "is_special": self.is_special,
            "browser": self.browser.value,
            "download_tool": self.download_tool.value,
        }
        try:
            with open(self.config_path, "w", encoding="utf-8") as f:
                json.dump(config, f, indent=2)
        except Exception as e:
            print(f"保存配置失败: {e}")


if __name__ == "__main__":
    ft.run(main=CourseraHub)
