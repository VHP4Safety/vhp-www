VENV := .venv
PY := $(VENV)/bin/python

.PHONY: serve build clean

# Live preview with auto-reload on http://localhost:5000
serve: $(VENV)/.installed
	$(VENV)/bin/flask --app app run --debug

# Static site into build/ (what GitHub Pages publishes)
build: $(VENV)/.installed
	$(PY) freeze.py

clean:
	rm -rf build

$(VENV)/.installed: requirements.txt
	python3 -m venv $(VENV)
	$(VENV)/bin/pip install -q -r requirements.txt
	touch $@
