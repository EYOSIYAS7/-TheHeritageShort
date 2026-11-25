"""`.env` is the only place keys are read from; empty values count as missing."""

from __future__ import annotations

from pathlib import Path

from pipeline.env import load_env


def test_env_file_values_are_read_and_comments_blanks_and_empty_values_dropped(tmp_path: Path) -> None:
    path = tmp_path / ".env"
    path.write_text(
        '# a comment\n\nGEMINI_API_KEY=abc123\nCLOUDFLARE_ACCOUNT_ID=\nKAGGLE_KEY="quoted value"\nexport KAGGLE_USERNAME=me\n',
        encoding="utf-8",
    )

    assert load_env(path) == {"GEMINI_API_KEY": "abc123", "KAGGLE_KEY": "quoted value", "KAGGLE_USERNAME": "me"}


def test_missing_env_file_means_no_keys(tmp_path: Path) -> None:
    assert load_env(tmp_path / ".env") == {}
