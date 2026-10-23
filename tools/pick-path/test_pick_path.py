"""Tests for home/dot_local/bin/executable_pick-path (run: pytest tools/pick-path)."""

from __future__ import annotations

import os
from importlib.machinery import SourceFileLoader
from importlib.util import module_from_spec, spec_from_loader
from pathlib import Path

import pytest

SCRIPT = Path(__file__).resolve().parents[2] / "home/dot_local/bin/executable_pick-path"
loader = SourceFileLoader("pick_path", str(SCRIPT))
pick_path = module_from_spec(spec_from_loader("pick_path", loader))
loader.exec_module(pick_path)


def run(capsys: pytest.CaptureFixture[str], base: Path, text: str, *extra: str) -> tuple[int, str]:
    code = pick_path.main(
        ["--base", str(base), "--default", "stamp", "--ext", "png", "--input", text, *extra]
    )
    return code, capsys.readouterr().out.strip()


@pytest.fixture(autouse=True)
def no_notifications(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(pick_path, "notify", lambda message: None)


@pytest.mark.parametrize(
    ("text", "expected"),
    [
        ("shot", "shot.png"),
        ("shot.png", "shot.png"),
        ("shot.PNG", "shot.PNG"),
        ("with space", "with space.png"),
        ("v1.2 notes", "v1.2 notes.png"),
        ("foo/bar", "foo/bar.png"),
        ("a b/c d", "a b/c d.png"),
        ("foo/", "foo/stamp.png"),
        ("foo/../bar", "bar.png"),
        ("  padded  ", "padded.png"),
    ],
)
def test_relative_names(capsys, tmp_path, text, expected):
    code, out = run(capsys, tmp_path, text)
    assert code == 0
    assert out == str(tmp_path / expected)
    assert (tmp_path / expected).parent.is_dir()


def test_absolute_path(capsys, tmp_path):
    code, out = run(capsys, tmp_path / "base", str(tmp_path / "elsewhere/x"))
    assert (code, out) == (0, str(tmp_path / "elsewhere/x.png"))


def test_tilde(capsys, tmp_path, monkeypatch):
    monkeypatch.setenv("HOME", str(tmp_path))
    code, out = run(capsys, tmp_path / "base", "~/x")
    assert (code, out) == (0, str(tmp_path / "x.png"))


def test_existing_directory_gets_default_name(capsys, tmp_path):
    (tmp_path / "dir").mkdir()
    assert run(capsys, tmp_path, "dir") == (0, str(tmp_path / "dir/stamp.png"))


def test_other_extension_refused(capsys, tmp_path):
    assert run(capsys, tmp_path, "shot.jpg")[0] == pick_path.REFUSED
    assert not any(tmp_path.iterdir())


def test_unwritable_directory_refused(capsys, tmp_path):
    locked = tmp_path / "locked"
    locked.mkdir()
    locked.chmod(0o555)
    try:
        if os.access(locked, os.W_OK):
            pytest.skip("running as root")
        assert run(capsys, tmp_path, "locked/sub/x")[0] == pick_path.REFUSED
        assert not (locked / "sub").exists()
    finally:
        locked.chmod(0o755)


def test_root_owned_path_refused(capsys, tmp_path):
    assert run(capsys, tmp_path, "/usr/x")[0] == pick_path.REFUSED


def test_file_as_directory_refused(capsys, tmp_path):
    (tmp_path / "file").write_text("")
    assert run(capsys, tmp_path, "file/x")[0] == pick_path.REFUSED


def test_existing_file_refused_without_prompt(capsys, tmp_path):
    (tmp_path / "shot.png").write_text("")
    assert run(capsys, tmp_path, "shot")[0] == pick_path.REFUSED


def test_overwrite_prompt(capsys, tmp_path, monkeypatch):
    (tmp_path / "old.png").write_text("")
    answers = iter(["old", "no", "old", "yes"])
    prompts = []

    def fake_ask(prompt, prefill="", choices=None, output=""):
        prompts.append((prompt, prefill, choices))
        return next(answers)

    monkeypatch.setattr(pick_path, "ask", fake_ask)
    code = pick_path.main(["--base", str(tmp_path), "--default", "stamp", "--ext", "png"])
    assert (code, capsys.readouterr().out.strip()) == (0, str(tmp_path / "old.png"))
    assert prompts[1] == ("Overwrite old.png?", "", ["no", "yes"])
    assert prompts[2][1] == "old"  # "no" goes back to the name prompt with the typed text


def test_cancel(capsys, tmp_path, monkeypatch):
    monkeypatch.setattr(pick_path, "ask", lambda *a, **k: None)
    assert pick_path.main(["--base", str(tmp_path)]) == pick_path.CANCELLED
    assert capsys.readouterr().out == ""
