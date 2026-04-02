#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Authors and copyright:
#     © 2012-2013, John Lehmann (first last at geemail dotcom or @jplehmann)
#     © 2012-2020, Rogério Theodoro de Brito
#     © 2013, Jonas De Taeye (first dt at fastmail fm)
#
# Contributions are welcome, but please add new unit tests to test your changes
# and/or features.  Also, please try to make changes platform independent and
# backward compatible.
#
# Legalese:
#
#  This program is free software: you can redistribute it and/or modify it
#  under the terms of the GNU Lesser General Public License as published by
#  the Free Software Foundation, either version 3 of the License, or (at your
#  option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program.  If not, see <http://www.gnu.org/licenses/>.


"""
Module for downloading lecture resources such as videos for Coursera classes.

Given a class name, username and password, it scrapes the course listing
page to get the section (week) and lecture names, and then downloads the
related materials into appropriately named files and directories.

Examples:
  coursera-helper -u <user> -p <passwd> saas
  coursera-helper -u <user> -p <passwd> -l listing.html -o saas --skip-download

For further documentation and examples, visit the project's home at:
  https://github.com/csyezheng/coursera
"""


import logging
import os
import shutil
import time

# Test versions of some critical modules.
# We may, perhaps, want to move these elsewhere.
import bs4
import requests
import six
from packaging.version import Version as V

from coursera_helper import __version__
from coursera_helper.cauth import cauth_by_cookie, cauth_by_login

from .api import expand_specializations
from .commandline import parse_args
from .cookies import AuthenticationFailed, ClassNotFound, TLSAdapter
from .define import PATH_CACHE
from .downloaders import get_downloader
from .extractors import CourseraExtractor
from .parallel import ConsecutiveDownloader, ParallelDownloader
from .utils import is_debug_run, mkdir_p, print_ssl_error_message, slurp_json, spit_json
from .workflow import CourseraDownloader

# URL containing information about outdated modules
_SEE_URL = " See https://github.com/csyezheng/coursera/issues/139"

assert V(requests.__version__) >= V("2.4"), "Upgrade requests!" + _SEE_URL
assert V(six.__version__) >= V("1.5"), "Upgrade six!" + _SEE_URL
assert V(bs4.__version__) >= V("4.1"), "Upgrade bs4!" + _SEE_URL


def get_session():
    """
    Create a session with TLS v1.2 certificate.
    """

    session = requests.Session()
    session.mount("https://", TLSAdapter())

    return session


def list_courses(session, args):
    """
    List enrolled courses.

    @param session: session.
    @type session: session

    @param args: Command-line arguments.
    @type args: namedtuple
    """
    extractor = CourseraExtractor(session)
    courses = extractor.list_courses()
    logging.info("Found %d courses", len(courses))
    for course in courses:
        logging.info(course)


_course_downloader_instance = None
_file_downloader_instance = None
_extractor_instance = None


def download_on_demand_class(session, args, class_name):
    """
    Download all requested resources from the on-demand class given
    in class_name.

    @return: Tuple of (bool, bool), where the first bool indicates whether
        errors occurred while parsing syllabus, the second bool indicates
        whether the course appears to be completed.
    @rtype: (bool, bool)
    """
    global _course_downloader_instance
    global _file_downloader_instance
    global _extractor_instance

    error_occurred = False
    extractor = CourseraExtractor(session)
    # 保存extractor实例以便取消
    _extractor_instance = extractor

    cached_syllabus_filename = "%s-syllabus-parsed.json" % class_name
    if args.cache_syllabus and os.path.isfile(cached_syllabus_filename):
        modules = slurp_json(cached_syllabus_filename)
    else:
        error_occurred, modules = extractor.get_modules(
            class_name,
            args.reverse,
            args.unrestricted_filenames,
            args.subtitle_language,
            args.video_resolution,
            args.download_quizzes,
            args.mathjax_cdn_url,
            args.download_notebooks,
        )

    if is_debug_run or args.cache_syllabus():
        spit_json(modules, cached_syllabus_filename)

    if args.only_syllabus:
        return error_occurred, False

    downloader = get_downloader(session, class_name, args)
    # 保存文件下载器实例以便取消
    _file_downloader_instance = downloader

    downloader_wrapper = (
        ParallelDownloader(downloader, args.jobs)
        if args.jobs > 1
        else ConsecutiveDownloader(downloader)
    )

    # obtain the resources

    ignored_formats = []
    if args.ignore_formats:
        ignored_formats = args.ignore_formats.split(",")

    course_downloader = CourseraDownloader(
        downloader_wrapper,
        commandline_args=args,
        class_name=class_name,
        path=args.path,
        ignored_formats=ignored_formats,
        disable_url_skipping=args.disable_url_skipping,
    )

    # 保存全局实例以便取消
    _course_downloader_instance = course_downloader

    completed = course_downloader.download_modules(modules)

    # Print skipped URLs if any
    if course_downloader.skipped_urls:
        print_skipped_urls(course_downloader.skipped_urls)

    # Print failed URLs if any
    # FIXME: should we set non-zero exit code if we have failed URLs?
    if course_downloader.failed_urls:
        print_failed_urls(course_downloader.failed_urls)

    return error_occurred, completed


def cancel_download():
    """取消当前下载"""
    global _course_downloader_instance
    global _file_downloader_instance
    global _extractor_instance

    logging.info("Download cancellation requested")

    # 取消extractor
    if _extractor_instance:
        # 检查是否有set_cancel_flag方法
        if hasattr(_extractor_instance, "set_cancel_flag"):
            _extractor_instance.set_cancel_flag(True)
            logging.info("Extractor cancellation requested")

    # 取消课程下载器
    if _course_downloader_instance:
        _course_downloader_instance.cancel()

    # 取消文件下载器
    if _file_downloader_instance:
        # 检查是否有set_cancel_flag方法
        if hasattr(_file_downloader_instance, "set_cancel_flag"):
            _file_downloader_instance.set_cancel_flag(True)
            logging.info("File downloader cancellation requested")

    return True


def print_skipped_urls(skipped_urls):
    logging.info(
        "The following URLs (%d) have been skipped and not " "downloaded:",
        len(skipped_urls),
    )
    logging.info(
        "(if you want to download these URLs anyway, please "
        'add "--disable-url-skipping" option)'
    )
    logging.info("-" * 80)
    for url in skipped_urls:
        logging.info(url)
    logging.info("-" * 80)


def print_failed_urls(failed_urls):
    logging.info("The following URLs (%d) could not be downloaded:", len(failed_urls))
    logging.info("-" * 80)
    for url in failed_urls:
        logging.info(url)
    logging.info("-" * 80)


def download_class(session, args, class_name):
    """
    Try to download on-demand class.

    @return: Tuple of (bool, bool), where the first bool indicates whether
        errors occurred while parsing syllabus, the second bool indicates
        whether the course appears to be completed.
    @rtype: (bool, bool)
    """
    logging.debug("Downloading new style (on demand) class %s", class_name)
    return download_on_demand_class(session, args, class_name)


def main(session=None, args=None):
    """
    Main entry point for execution as a program (instead of as a module).
    """

    if args is None:
        args = parse_args()
    logging.info("coursera_dl version %s", __version__)
    completed_classes = []
    classes_with_errors = []

    mkdir_p(PATH_CACHE, 0o700)
    if args.clear_cache:
        shutil.rmtree(PATH_CACHE)

    if session is None:
        session = get_session()
    if args.cookies_cauth and args.cookies_cauth != "dummy_cauth":
        session.cookies.set("CAUTH", args.cookies_cauth)
    elif args.browser_cookie:
        cauth = cauth_by_cookie()
        session.cookies.set("CAUTH", cauth)
    elif args.username and args.password:
        cauth = cauth_by_login(args.username, args.password, headless=args.headless)
        session.cookies.set("CAUTH", cauth)

    if args.list_courses:
        logging.info("Listing enrolled courses")
        list_courses(session, args)
        return

    if args.specialization:
        args.class_names = expand_specializations(session, args.class_names)

    for class_index, class_name in enumerate(args.class_names):
        try:
            logging.info(
                "Downloading class: %s (%d / %d)",
                class_name,
                class_index + 1,
                len(args.class_names),
            )
            error_occurred, completed = download_class(session, args, class_name)
            if completed:
                completed_classes.append(class_name)
            if error_occurred:
                classes_with_errors.append(class_name)
        except requests.exceptions.HTTPError as e:
            logging.error("HTTPError %s", e)
            if is_debug_run():
                logging.exception("HTTPError %s", e)
        except requests.exceptions.SSLError as e:
            logging.error("SSLError %s", e)
            print_ssl_error_message(e)
            if is_debug_run():
                raise
        except ClassNotFound as e:
            logging.error("Could not find class: %s", e)
        except AuthenticationFailed as e:
            logging.error("Could not authenticate: %s", e)
        except Exception as e:
            logging.error("error: %s", e)

        if class_index + 1 != len(args.class_names):
            logging.info(
                "Sleeping for %d seconds before downloading next course. "
                "You can change this with --download-delay option.",
                args.download_delay,
            )
            time.sleep(args.download_delay)

    if completed_classes:
        logging.info("-" * 80)
        logging.info("Classes which appear completed: " + " ".join(completed_classes))

    if classes_with_errors:
        logging.info("-" * 80)
        logging.info(
            "The following classes had errors during the syllabus"
            " parsing stage. You may want to review error messages and"
            " courses (sometimes enrolling to the course or switching"
            " session helps):"
        )
        for class_name in classes_with_errors:
            logging.info(
                "%s (https://www.coursera.org/learn/%s)", class_name, class_name
            )


if __name__ == "__main__":
    main()
