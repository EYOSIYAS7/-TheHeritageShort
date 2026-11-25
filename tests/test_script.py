"""Script stage at the pipeline seam: Amharic drafts written back into the storyboard."""

from __future__ import annotations

from pipeline import run
from tests.conftest import FakeSpeech, FakeText, Project, no_sleep, providers


def test_pinned_line_is_never_sent_or_overwritten_and_drafts_are_marked_unreviewed(project: Project) -> None:
    text = FakeText()

    run.film(project.root, providers(FakeSpeech(), text), sleep=no_sleep)

    # Line b is pinned (ነገ አባባ ነገ): only a and c reach the text model.
    assert [p.rsplit("English: ", 1)[-1] for p in text.prompts] == [
        "Let's talk tomorrow, Dad.", "Not every tomorrow is promised.",
    ]
    lines = {line["id"]: line for line in project.read()["narration"]}
    assert lines["b"]["am"] == "ነገ አባባ ነገ" and lines["b"]["am_reviewed"] is True
    assert lines["a"]["am"] == "AM:Let's talk tomorrow, Dad."
    assert lines["a"]["am_reviewed"] is False
    assert lines["a"]["am_from_en"] == "Let's talk tomorrow, Dad."
