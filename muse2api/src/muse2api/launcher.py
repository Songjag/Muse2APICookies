"""Select a persisted cookie session before starting the Python server."""

from __future__ import annotations

import asyncio
import getpass
import re
from pathlib import Path

import uvicorn

from .__main__ import save_login
from .accounts.store import JsonAccountStore
from .app import create_app
from .config import Settings, get_settings
from .log import setup_logging
from .upstream.muse import missing_session_cookies

SESSION_PATTERN = re.compile(r"session_coookie_([1-9][0-9]*)\.json")


def session_files(data_dir: Path) -> list[Path]:
    return sorted(
        (p for p in data_dir.glob("session_coookie_*.json")
         if p.is_file() and SESSION_PATTERN.fullmatch(p.name)),
        key=lambda p: int(SESSION_PATTERN.fullmatch(p.name)[1]),
    )


async def validate_session(path: Path) -> None:
    accounts = await JsonAccountStore(path).load()
    if len(accounts) != 1 or missing_session_cookies(accounts[0].cookies):
        raise ValueError("Invalid session")


def select_session(settings: Settings) -> Path:
    while True:
        files = session_files(settings.data_dir)
        print("\nCác phiên cookie đã lưu:")
        for index, path in enumerate(files, 1):
            print(f"  {index}. {path.name}")
        if not files:
            print("  Chưa có phiên nào.")
        print("  0. Nhập cookie để tạo phiên mới")
        choice = input("Chọn số phiên (Enter = tạo mới): ").strip() or "0"
        if choice == "0":
            number = max((int(SESSION_PATTERN.fullmatch(p.name)[1]) for p in files), default=0) + 1
            path = settings.data_dir / f"session_coookie_{number}.json"
            raw = getpass.getpass("Dán Cookie header muse.ai (ẩn nội dung): ")
            candidate = settings.model_copy(update={"account_store_file": path})
            try:
                asyncio.run(save_login(candidate, raw, f"Session {number}"))
            except ValueError:
                print("Cookie cần có hatch_sess và hatch_native_auth_device với giá trị không rỗng.")
                continue
            return path
        if not choice.isdecimal() or not 1 <= int(choice) <= len(files):
            print("Lựa chọn không hợp lệ. Vui lòng nhập số trong danh sách.")
            continue
        path = files[int(choice) - 1]
        try:
            asyncio.run(validate_session(path))
        except (ValueError, OSError):
            print("Không đọc được phiên hoặc cookie không hợp lệ. Hãy chọn phiên khác hoặc tạo mới.")
            continue
        return path


def main() -> None:
    settings = get_settings().model_copy(update={"driver": "browser"})
    try:
        settings.account_store_file = select_session(settings)
    except (EOFError, KeyboardInterrupt):
        print("\nĐã hủy khởi động.")
        return
    except OSError:
        raise SystemExit("Không thể lưu phiên. Hãy kiểm tra quyền truy cập thư mục data.") from None
    setup_logging(settings.log_level)
    app = create_app(settings)
    print(f"Đang dùng: {settings.accounts_file}")
    print(f"Server: http://{settings.host}:{settings.port}")
    if settings.key_file.is_file():
        print(f"API key: {settings.key_file}")
    uvicorn.run(app, host=settings.host, port=settings.port, log_level=settings.log_level.lower())
