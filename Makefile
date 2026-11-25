# One command: `make film` builds the film from storyboard.json.
# A virtualenv with the Python dependencies is created on first use.
# Needs: python3 (with venv), ffmpeg/ffprobe on PATH.

VENV := .venv
PY := $(VENV)/bin/python

.PHONY: film test typecheck check

## Build the film into outputs/film/ (validates storyboard.json first)
film: $(VENV)/.deps
	$(PY) -m pipeline film

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
