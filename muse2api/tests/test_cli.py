from unittest.mock import patch

import pytest

from muse2api.__main__ import main, save_login
from muse2api.accounts.model import Account, AccountStatus
from muse2api.accounts.store import JsonAccountStore
from muse2api.config import Settings


@pytest.mark.asyncio
async def test_login_updates_rotated_session_and_preserves_other_accounts(tmp_path):
    settings = Settings(_env_file=None, data_dir=tmp_path)
    store = JsonAccountStore(settings.accounts_file)
    old = Account(cookies={"hatch_sess": "old", "hatch_native_auth_device": "device"},
                  status=AccountStatus.INVALID, enabled=False, meta={"quota": {}})
    other = Account(cookies={"hatch_native_auth_device": "other"})
    await store.save([old, other])
    await save_login(settings, "Cookie: hatch_sess=new==; hatch_native_auth_device=device", "Mine")
    accounts = await store.load()
    assert len(accounts) == 2
    assert accounts[0].id == old.id
    assert accounts[0].cookies["hatch_sess"] == "new=="
    assert accounts[0].enabled
    assert accounts[0].status == AccountStatus.ACTIVE
    assert accounts[0].meta == {}
    assert accounts[1] == other
    assert settings.accounts_file.stat().st_mode & 0o777 == 0o600


@pytest.mark.asyncio
async def test_incomplete_cookie_does_not_write(tmp_path):
    settings = Settings(_env_file=None, data_dir=tmp_path)
    with pytest.raises(ValueError, match="hatch_native_auth_device"):
        await save_login(settings, "hatch_sess=secret", "Mine")
    assert not settings.accounts_file.exists()


def test_login_starts_browser_server_without_printing_cookie(tmp_path, capsys):
    settings = Settings(_env_file=None, data_dir=tmp_path)
    cookie = "hatch_sess=secret; hatch_native_auth_device=device"
    with patch("muse2api.__main__.get_settings", return_value=settings), \
         patch("muse2api.__main__.getpass.getpass", return_value=cookie), \
         patch("muse2api.__main__.create_app") as create, \
         patch("muse2api.__main__.uvicorn.run") as run:
        main(["--login"])
    assert settings.driver == "browser"
    create.assert_called_once_with(settings)
    run.assert_called_once()
    assert "secret" not in capsys.readouterr().out


def test_invalid_login_does_not_start_server(tmp_path, capsys):
    settings = Settings(_env_file=None, data_dir=tmp_path)
    with patch("muse2api.__main__.get_settings", return_value=settings), \
         patch("muse2api.__main__.getpass.getpass", return_value="hatch_sess=secret"), \
         patch("muse2api.__main__.uvicorn.run") as run, \
         pytest.raises(SystemExit) as exc:
        main(["--login"])
    assert exc.value.code == 2
    run.assert_not_called()
    assert "secret" not in capsys.readouterr().err
