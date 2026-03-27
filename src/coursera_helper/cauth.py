import logging
import sys
import random
import platform
import browser_cookie3
from playwright.sync_api import sync_playwright


def cauth_by_login(username, password, headless=True):
    with sync_playwright() as playwright:
        try:
            if platform.system() == 'Windows':
                browser = playwright.chromium.launch(channel="msedge", headless=headless)
            elif platform.system() == 'Linux':
                browser = playwright.firefox.launch(headless=headless)
            elif platform.system() == 'Darwin':
                browser = playwright.webkit.launch(headless=headless)
            else:
                browser = playwright.chromium.launch(channel="chrome", headless=headless)
        except AttributeError:
            logging.info('Please run "playwright install" in terminal and then try again!')
            sys.exit()

        context = browser.new_context(
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) '
                       'Chrome/117.0.0.0 Safari/537.36',
        )
        context.add_init_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")

        page = context.new_page()

        page.goto("https://www.coursera.org/", timeout=0)
        page.click('a[href*="/?authMode=login"]')

        email_elem = page.locator('#email')
        password_elem = page.locator('#password')

        email_elem.press_sequentially(username, delay=random.random() * 1000)
        password_elem.press_sequentially(password, delay=random.random() * 1000)

        page.locator('button[type*="submit"]').click()

        page.wait_for_selector('p[data-e2e="UserPortraitFullName"]', timeout=0)

        cookies = context.cookies('https://www.coursera.org/')
        cauth = ''
        cookie_dict = {cookie['name']: cookie['value'] for cookie in cookies}
        if 'CAUTH' in cookie_dict:
            cauth = cookie_dict['CAUTH']
        browser.close()
        return cauth


def cauth_by_cookie():
    domain = 'coursera.org'
    browsers = ['chrome', 'chromium', 'edge', 'firefox', 'safari']
    for browser in browsers:
        try:
            statement = 'browser_cookie3.{}(domain_name="{}")'.format(browser, domain)
            cookies = eval(statement)
            cookie_dict = {cookie.name: cookie.value for cookie in cookies}
            if 'CAUTH' in cookie_dict:
                cauth = cookie_dict['CAUTH']
                return cauth
        except browser_cookie3.BrowserCookieError:
            pass
