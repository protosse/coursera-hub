import logging
import os
import sys
import threading

from constants import AuthMethod
from coursera_helper.cauth import cauth_by_cookie, cauth_by_login
from coursera_helper.commandline import parse_args
from coursera_helper.coursera_dl import cancel_download, get_session
from coursera_helper.coursera_dl import main as m
from coursera_helper.extractors import CourseraExtractor


class CourseraHelperWrapper:
    def __init__(self):
        self.session = get_session()
        logging.basicConfig(level=logging.INFO, format="%(message)s")

    def authenticate(self, auth_method: AuthMethod, **kwargs):
        """
        认证方法
        auth_method: 'cauth', 'browser', 'credentials'
        kwargs: 根据auth_method提供相应的参数
        """
        try:
            if auth_method == AuthMethod.CAUTH:
                cauth = kwargs.get("cauth")
                if cauth:
                    self.session.cookies.set("CAUTH", cauth)
                    return True, "CAUTH认证成功"
            elif auth_method == AuthMethod.CREDENTIALS:
                username = kwargs.get("username")
                password = kwargs.get("password")
                if username and password:
                    cauth = cauth_by_login(username, password, headless=True)
                    self.session.cookies.set("CAUTH", cauth)
                    return True, "用户名密码认证成功"
            elif auth_method == AuthMethod.BROWSER:
                cauth = cauth_by_cookie()
                self.session.cookies.set("CAUTH", cauth)
                return True, "浏览器Cookie认证成功"
            return False, "认证失败：缺少必要参数"
        except Exception as e:
            return False, f"认证失败: {str(e)}"

    def list_courses(self):
        try:
            extractor = CourseraExtractor(self.session)
            courses = extractor.list_courses()
            return courses

        except Exception as e:
            return f"列出课程失败: {str(e)}"

    def download_course(self, course_name, download_path, cancel_flag=None, **options):
        """
        下载课程
        course_name: 课程名称
        download_path: 下载路径
        cancel_flag: 取消标志（可调用对象，返回True表示取消）
        options: 下载选项
        """
        try:
            # 使用parse_args获取完整的args对象
            # 创建一个简单的命令行参数列表

            sys.argv = ["coursera_dl", "--cauth", "dummy_cauth", "dummy_course"]
            args = parse_args()

            # 修改需要的属性
            args.class_names = [course_name]
            args.path = download_path
            for option, value in options.items():
                setattr(args, option, value)

            # 确保下载路径存在
            if len(download_path) > 0:
                os.makedirs(download_path, exist_ok=True)

            yield f"开始下载课程: {course_name}"
            yield f"是否是专业课程: {args.specialization}"
            yield f"下载路径: {download_path}"
            yield f"字幕语言: {args.subtitle_language}"

            # 启动一个监控线程，检查取消请求
            def monitor_cancel():
                while not cancel_flag():
                    import time

                    time.sleep(0.1)
                # 调用取消函数
                cancel_download()

            # 启动监控线程
            cancel_thread = threading.Thread(target=monitor_cancel, daemon=True)
            cancel_thread.start()

            m(self.session, args)
            return True

        except Exception as e:
            # 检查是否取消
            if cancel_flag and cancel_flag():
                yield "下载已取消"
                return False
            yield f"下载失败: {str(e)}"
            return False
