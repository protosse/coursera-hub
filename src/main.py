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

        self.langs = list(ALL_Language.keys())
        self.browsers = list(ALL_BROWERS.keys())

        # 全局变量
        self.auth_method = "cauth"
        self.cauth = ""
        self.username = ""
        self.password = ""
        self.course_name = ""
        self.download_path = str(Path.home())
        self.subtitle_language1 = self.langs[0]
        self.subtitle_language2 = self.langs[1]
        self.is_special = False
        self.browser = "edge"

        # 创建输出日志控件的ref
        self.output_list_view = ft.Ref[ft.ListView]()
        self.auth_details = ft.Row()
        self.download_path_field = ft.Ref[ft.TextField]()

        # 创建消息队列用于线程间通信
        import queue

        self.message_queue = queue.Queue()

        # 下载线程和取消标志
        self.download_thread = None
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
                            value=self.auth_method,
                            on_change=self.auth_method_changed,
                            content=ft.Row(
                                controls=[
                                    ft.Radio(
                                        label="CAUTH",
                                        value="cauth",
                                    ),
                                    ft.Radio(
                                        label="浏览器Cookie",
                                        value="browser",
                                    ),
                                    ft.Radio(
                                        label="用户名密码",
                                        value="credentials",
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
                        hint_text="输入课程名称，留空则列出所有课程",
                        value=self.course_name,
                        on_change=self.course_name_changed,
                    ),
                    ft.Checkbox(
                        label="专项课程",
                        value=self.is_special,
                        on_change=self.is_special_changed,
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
                        value=self.subtitle_language1,
                        options=[
                            ft.dropdownm2.Option(key=v, text=v) for v in self.langs
                        ],
                        on_change=self.subtitle_language1_changed,
                    ),
                    ft.DropdownM2(
                        label="字幕2",
                        value=self.subtitle_language2,
                        options=[
                            ft.dropdownm2.Option(key=v, text=v) for v in self.langs
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
        self.auth_method = e.control.value
        self.update_auth_details()
        self.save_config()

    def update_auth_details(self):
        self.auth_details.controls.clear()

        if self.auth_method == "cauth":
            self.auth_details.controls.append(
                ft.TextField(
                    label="CAUTH值",
                    hint_text="输入CAUTH值",
                    value=self.cauth,
                    on_change=self.cauth_changed,
                )
            )
        elif self.auth_method == "credentials":
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
                    password=True,
                    on_change=self.password_changed,
                )
            )
        elif self.auth_method == "browser":
            self.auth_details.controls.append(
                ft.DropdownM2(
                    label="浏览器",
                    value=self.browser,
                    options=[
                        ft.dropdownm2.Option(key=v, text=v) for v in self.browsers
                    ],
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

    def browser_change(self, e):
        self.browser = e.control.value
        self.save_config()

    def subtitle_language1_changed(self, e):
        self.subtitle_language1 = e.control.value
        self.save_config()

    def subtitle_language2_changed(self, e):
        self.subtitle_language2 = e.control.value
        self.save_config()

    def list_courses(self, e):
        self.append_output("正在列出课程...")

        # 先进行认证
        if self.auth_method == "cauth" and self.cauth:
            success, message = self.coursera_helper.authenticate(
                "cauth", cauth=self.cauth
            )
            self.append_output(message)
            if not success:
                return
        elif self.auth_method == "credentials" and self.username and self.password:
            success, message = self.coursera_helper.authenticate(
                "credentials", username=self.username, password=self.password
            )
            self.append_output(message)
            if not success:
                return
        elif self.auth_method == "browser":
            success, message = self.coursera_helper.authenticate("browser")
            self.append_output(message)
            if not success:
                return
        else:
            self.append_output("错误：请输入完整的认证信息")
            return

        # 调用coursera-helper的list_courses方法
        courses = self.coursera_helper.list_courses()

        if isinstance(courses, list):
            self.append_output("列出课程成功！")
            for course in courses:
                self.append_output(course)
        else:
            self.append_output(f"列出课程失败: {courses}")

    async def download_course(self, e):
        if not self.course_name:
            self.append_output("错误：请输入课程名称")
            return

        # 在后台线程中运行下载，避免阻塞UI
        import threading

        def run_download():
            # 先进行认证
            if self.auth_method == "cauth" and self.cauth:
                success, message = self.coursera_helper.authenticate(
                    "cauth", cauth=self.cauth
                )
                # 将消息放入队列
                self.message_queue.put(message)
                if not success:
                    return
            elif self.auth_method == "credentials" and self.username and self.password:
                success, message = self.coursera_helper.authenticate(
                    "credentials", username=self.username, password=self.password
                )
                self.message_queue.put(message)
                if not success:
                    return
            elif self.auth_method == "browser":
                success, message = self.coursera_helper.authenticate("browser")
                self.message_queue.put(message)
                if not success:
                    return
            else:
                self.message_queue.put("错误：请输入完整的认证信息")
                return

            # 调用coursera-helper的download_course方法
            langs = [
                ALL_Language[v]
                for v in [self.subtitle_language1, self.subtitle_language2]
            ]
            download_options = {
                "subtitle_language": ",".join(langs),
                "video_resolution": "720p",
                "download_quizzes": True,
                "download_notebooks": True,
            }

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
        try:
            # 尝试从队列中获取消息（非阻塞）
            while not self.message_queue.empty():
                message = self.message_queue.get(block=False)
                self.append_output(message)
                self.message_queue.task_done()
        except:
            pass

        # 设置定时器，继续处理队列
        self.page.run_task(self.process_message_queue)

    def append_output(self, text):
        # 使用ref直接获取ListView控件
        if self.output_list_view.current:
            # 添加新的日志条目
            self.output_list_view.current.controls.append(ft.Text(text))
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
                    self.auth_method = config.get("auth_method", "cauth")
                    self.cauth = config.get("cauth", "")
                    self.username = config.get("username", "")
                    self.password = config.get("password", "")
                    self.course_name = config.get("course_name", "")
                    self.download_path = config.get("download_path", str(Path.home()))
                    self.subtitle_language1 = config.get(
                        "subtitle_language1", self.langs[0]
                    )
                    self.subtitle_language2 = config.get(
                        "subtitle_language2", self.langs[1]
                    )
                    self.is_special = config.get("is_special", False)
                    self.browser = config.get("browser", "edge")
            except Exception as e:
                print(f"加载配置失败: {e}")

    def save_config(self):
        """保存配置"""
        config = {
            "auth_method": self.auth_method,
            "cauth": self.cauth,
            "username": self.username,
            "password": self.password,
            "course_name": self.course_name,
            "download_path": self.download_path,
            "subtitle_language1": self.subtitle_language1,
            "subtitle_language2": self.subtitle_language2,
            "is_special": self.is_special,
            "browser": self.browser,
        }
        try:
            with open(self.config_path, "w", encoding="utf-8") as f:
                json.dump(config, f, indent=2)
        except Exception as e:
            print(f"保存配置失败: {e}")


if __name__ == "__main__":
    ft.run(main=CourseraHub)
