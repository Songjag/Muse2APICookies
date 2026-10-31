import asyncio
from unittest.mock import patch

from muse2api.accounts.store import JsonAccountStore
from muse2api.config import Settings
from muse2api.launcher import main, select_session, session_files

COOKIE = "hatch_sess=secret; hatch_native_auth_device=device"


def test_create_then_select_and_persist_rotation(tmp_path):
    settings = Settings(_env_file=None, data_dir=tmp_path)
    with patch("builtins.input", return_value="0"), \
         patch("muse2api.launcher.getpass.getpass", return_value=COOKIE):
        first = select_session(settings)
        second = select_session(settings)
    assert first.name == "session_coookie_1.json"
    assert second.name == "session_coookie_2.json"
    with patch("builtins.input", side_effect=["invalid", "3", "2"]), \
         patch("muse2api.launcher.getpass.getpass") as prompt:
        selected = select_session(settings)
    assert selected == second
    prompt.assert_not_called()
    settings.account_store_file = selected

    async def rotate():
        store = JsonAccountStore(settings.accounts_file)
        accounts = await store.load()
        assert len(accounts) == 1
        accounts[0].cookies["hatch_sess"] = "rotated"
        await store.save(accounts)
        assert (await store.load())[0].cookies["hatch_sess"] == "rotated"
        assert (await JsonAccountStore(first).load())[0].cookies["hatch_sess"] == "secret"
    asyncio.run(rotate())
    assert not (tmp_path / "accounts.json").exists()


def test_numeric_order_and_next_number_with_gaps(tmp_path):
    for name in ("session_coookie_10.json", "session_coookie_2.json", "session_coookie_bad.json"):
        (tmp_path / name).write_text("[]")
    assert [p.name for p in session_files(tmp_path)] == [
        "session_coookie_2.json", "session_coookie_10.json"]
    settings = Settings(_env_file=None, data_dir=tmp_path)
    with patch("builtins.input", side_effect=["1", "0", "0"]), \
         patch("muse2api.launcher.getpass.getpass", side_effect=["bad", COOKIE]):
        path = select_session(settings)
    assert path.name == "session_coookie_11.json"


def test_main_starts_with_selected_store(tmp_path, capsys):
    settings = Settings(_env_file=None, data_dir=tmp_path)
    with patch("muse2api.launcher.get_settings", return_value=settings), \
         patch("builtins.input", return_value=""), \
         patch("muse2api.launcher.getpass.getpass", return_value=COOKIE), \
         patch("muse2api.launcher.create_app") as create, \
         patch("muse2api.launcher.uvicorn.run") as run:
        main()
    actual = create.call_args.args[0]
    assert actual.driver == "browser"
    assert actual.accounts_file == tmp_path / "session_coookie_1.json"
    run.assert_called_once()
    assert "secret" not in capsys.readouterr().out


def test_cancel_does_not_start_server(tmp_path):
    with patch("muse2api.launcher.get_settings", return_value=Settings(_env_file=None, data_dir=tmp_path)), \
         patch("builtins.input", side_effect=KeyboardInterrupt), \
         patch("muse2api.launcher.uvicorn.run") as run:
        main()
    run.assert_not_called()
