"""Cookie import formats shared by the CLI and admin API."""

from __future__ import annotations

from ..errors import InvalidRequest


def parse_cookies(value: dict[str, str] | str | list[dict]) -> tuple[dict[str, str], dict[str, int]]:
    """Normalise the three cookie import formats into ``(cookies, cookie_expires)``.

    ``cookie_expires`` maps cookie name -> unix expiry seconds; only cookie-export
    lists carry expiry info, the other formats return an empty dict.
    """
    if isinstance(value, dict):
        return dict(value), {}
    if isinstance(value, str):
        cookies: dict[str, str] = {}
        for part in value.split(";"):
            part = part.strip()
            if not part or "=" not in part:
                continue
            name, _, val = part.partition("=")
            name = name.strip()
            if name:
                cookies[name] = val.strip()
        return cookies, {}
    if isinstance(value, list):
        cookies, expires = {}, {}
        for i, entry in enumerate(value):
            if not isinstance(entry, dict) or not entry.get("name"):
                raise InvalidRequest(f"cookies[{i}] must be an object with 'name' and 'value'")
            name = str(entry["name"])
            cookies[name] = str(entry.get("value", ""))
            exp = entry.get("expirationDate")
            if exp is not None:
                try:
                    expires[name] = int(float(exp))
                except (TypeError, ValueError):
                    raise InvalidRequest(f"cookies[{i}].expirationDate is not a number") from None
        return cookies, expires
    raise InvalidRequest("cookies must be a dict, a raw 'Cookie' header string, or a cookie-export list")

