from enum import Enum


class AuthMethod(Enum):
    """认证方法枚举"""

    CAUTH = "cauth"
    BROWSER = "browser"
    CREDENTIALS = "credentials"


class Language(Enum):
    """语言枚举"""

    ENGLISH = "英文"
    CHINESE = "中文"

    @property
    def code(self):
        match self:
            case Language.ENGLISH:
                return "en"
            case Language.CHINESE:
                return "zh-CN|zh-TW"


class Browser(Enum):
    """浏览器枚举"""

    CHROME = "chrome"
    CHROMIUM = "chromium"
    OPERA = "opera"
    OPERA_GX = "opera_gx"
    BRAVE = "brave"
    EDGE = "edge"
    VIVALDI = "vivaldi"
    FIREFOX = "firefox"
    LIBREWOLF = "librewolf"
    SAFARI = "safari"
