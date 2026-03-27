import logging
import os

from coursera_helper.cauth import cauth_by_cookie, cauth_by_login
from coursera_helper.coursera_dl import download_class, get_session


class CourseraHelperWrapper:
    def __init__(self):
        self.session = get_session()
        logging.basicConfig(level=logging.INFO, format="%(message)s")

    def authenticate(self, auth_method, **kwargs):
        """
        认证方法
        auth_method: 'cauth', 'browser', 'credentials'
        kwargs: 根据auth_method提供相应的参数
        """
        try:
            if auth_method == "cauth":
                cauth = kwargs.get("cauth")
                if cauth:
                    self.session.cookies.set("CAUTH", cauth)
                    return True, "CAUTH认证成功"
            elif auth_method == "credentials":
                username = kwargs.get("username")
                password = kwargs.get("password")
                if username and password:
                    cauth = cauth_by_login(username, password, headless=True)
                    self.session.cookies.set("CAUTH", cauth)
                    return True, "用户名密码认证成功"
            elif auth_method == "browser":
                cauth = cauth_by_cookie()
                self.session.cookies.set("CAUTH", cauth)
                return True, "浏览器Cookie认证成功"
            return False, "认证失败：缺少必要参数"
        except Exception as e:
            return False, f"认证失败: {str(e)}"

    def list_courses(self):
        try:
            # 直接使用CourseraExtractor来列出课程
            from coursera_helper.extractors import CourseraExtractor

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
            import sys
            import threading

            from coursera_helper.commandline import parse_args

            original_argv = sys.argv
            sys.argv = ["coursera_dl", "--cauth", "dummy_cauth", "dummy_course"]

            try:
                args = parse_args()
            finally:
                sys.argv = original_argv

            # 修改需要的属性
            args.subtitle_language = options.get("subtitle_language", "en")
            args.video_resolution = options.get("video_resolution", "720p")
            args.download_quizzes = options.get("download_quizzes", False)
            args.download_notebooks = options.get("download_notebooks", False)
            args.path = download_path

            # 确保下载路径存在
            os.makedirs(download_path, exist_ok=True)

            yield f"开始下载课程: {course_name}"
            yield f"下载路径: {download_path}"
            yield f"字幕语言: {args.subtitle_language}"
            yield f"视频分辨率: {args.video_resolution}"
            yield f"下载测验: {args.download_quizzes}"
            yield f"下载笔记本: {args.download_notebooks}"

            # 从coursera_dl模块导入取消函数
            from coursera_helper.coursera_dl import cancel_download

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

            # 执行下载
            error_occurred, completed = download_class(self.session, args, course_name)

            if completed:
                yield f"课程下载完成: {course_name}"
            else:
                yield f"课程下载失败或未完成: {course_name}"

            return completed

        except Exception as e:
            # 检查是否取消
            if cancel_flag and cancel_flag():
                yield "下载已取消"
                return False
            yield f"下载失败: {str(e)}"
            return False
