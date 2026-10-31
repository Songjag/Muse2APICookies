from __future__ import annotations

import argparse
import asyncio
import getpass

import uvicorn

from .accounts.cookies import parse_cookies
from .accounts.model import Account, AccountStatus
from .accounts.store import JsonAccountStore
from .app import create_app
from .config import Settings, get_settings
from .log import setup_logging
from .upstream.muse import missing_session_cookies


async def save_login(settings: Settings, raw_cookie: str, label: str) -> None:
    raw_cookie = raw_cookie.strip()
    if raw_cookie.lower().startswith("cookie:"):
        raw_cookie = raw_cookie.partition(":")[2].strip()
    cookies, expires = parse_cookies(raw_cookie)
    missing = missing_session_cookies(cookies)
    if missing:
        raise ValueError("Missing required cookies: " + ", ".join(missing))
    store = JsonAccountStore(settings.accounts_file)
    accounts = await store.load()
    # The device cookie identifies an existing login even after session rotation.
    account = next((a for a in accounts if a.cookies.get("hatch_native_auth_device")
                    == cookies["hatch_native_auth_device"]), None)
    if account is None:
        account = Account()
        accounts.append(account)
    account.label = label
    account.cookies = cookies
    account.cookie_expires = expires
    account.enabled = True
    account.status = AccountStatus.ACTIVE
    account.cooldown_until = 0
    account.last_error = None
    account.meta = {}
    await store.save(accounts)


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description="Run the muse2api Python server.")
    parser.add_argument("--login", action="store_true",
                        help="Prompt for a Cookie header, save the account, and use the browser driver.")
    parser.add_argument("--label", default="CLI login", help="Account label for --login.")
    parser.add_argument("--driver", choices=("mock", "browser", "http"),
                        help="Override the configured driver.")
    args = parser.parse_args(argv)
    settings = get_settings()
    if args.driver:
        settings.driver = args.driver
    elif args.login:
        settings.driver = "browser"
    if args.login:
        try:
            raw_cookie = getpass.getpass("Paste muse.ai Cookie header (hidden): ")
            asyncio.run(save_login(settings, raw_cookie, args.label))
        except (EOFError, KeyboardInterrupt):
            parser.exit(1, "\nLogin cancelled.\n")
        except ValueError:
            parser.error("Invalid login or account file. Supply a Cookie header containing "
                         "hatch_sess and hatch_native_auth_device with non-empty values.")
        print(f"Account saved in {settings.accounts_file}")
    setup_logging(settings.log_level)
    app = create_app(settings)
    print(f"muse2api listening on http://{settings.host}:{settings.port}  (driver={settings.driver})")
    if settings.key_file.is_file():
        print(f"auto-generated API key is stored in {settings.key_file}")
    uvicorn.run(app, host=settings.host, port=settings.port, log_level=settings.log_level.lower())


if __name__ == "__main__":
    main()
