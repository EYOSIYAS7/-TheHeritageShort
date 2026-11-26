# One command: `make film` builds the film from storyboard.json.
# A virtualenv with the Python dependencies is created on first use.
# Needs: python3 (with venv), ffmpeg/ffprobe on PATH.

VENV := .venv
PY := $(VENV)/bin/python

.PHONY: film gpu costs rough-cut radio-cut review voices test typecheck check

## Build the film into outputs/film/ (validates storyboard.json first)
film: $(VENV)/.deps
	$(PY) -m pipeline film

## Only the Kaggle GPU stages (score candidates, moving shots): fills the cache, renders nothing
gpu: $(VENV)/.deps
	$(PY) -m pipeline gpu

## Per-stage summary of runs.jsonl: calls, cache hits, latency, image list price
costs: $(VENV)/.deps
	$(PY) -m pipeline costs

## Rough cut: character sheet, keyframes and pan shots with narration, subtitles and music; 16:9 and 9:16
rough-cut: $(VENV)/.deps
	$(PY) -m pipeline rough-cut

## Radio cut (user test 1): narration, subtitles and placeholder music on a black screen; unreviewed Amharic allowed
radio-cut: $(VENV)/.deps
	$(PY) -m pipeline radio-cut

## List narration lines whose Amharic is not reviewed yet (English beside Amharic)
review: $(VENV)/.deps
	$(PY) -m pipeline review

## Voice trial: the trial line spoken by each candidate voice (narrator.voice_trial in storyboard.json)
voices: $(VENV)/.deps
	$(PY) -m pipeline voices

## Run the test suite (fake providers, real FFmpeg)
test: $(VENV)/.dev-deps
	$(PY) -m pytest -q

## Static type check
typecheck: $(VENV)/.dev-deps
	$(PY) -m mypy

check: typecheck test

$(VENV)/.deps: requirements.txt
	python3 -m venv $(VENV)
	$(PY) -m pip install -q -r requirements.txt
	touch $@

$(VENV)/.dev-deps: requirements-dev.txt requirements.txt
	python3 -m venv $(VENV)
	$(PY) -m pip install -q -r requirements-dev.txt
	touch $@ $(VENV)/.deps
