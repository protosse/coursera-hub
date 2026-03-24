import flet as ft


def _parse_bool(value) -> bool:
    if value is None:
        return False
    if isinstance(value, bool):
        return value
    s = str(value).strip().lower()
    return s in {"1", "true", "t", "yes", "y", "on"}


async def get_bool(key: str, default: bool = False) -> bool:
    raw = await ft.SharedPreferences().get(key)
    if raw is None:
        return default
    return _parse_bool(raw)


async def set_bool(key: str, value: bool) -> None:
    await ft.SharedPreferences().set(key, "1" if bool(value) else "0")
