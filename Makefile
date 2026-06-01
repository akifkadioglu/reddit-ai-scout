VENV := venv
PY := $(VENV)/bin/python
PIP := $(VENV)/bin/pip

# Parametreler (override: make run q="bitcoin" LIMIT=5 AI=1)
q ?=
LIMIT ?= 10
AI ?=
AI_FLAG := $(if $(AI),--ai,)

.PHONY: setup run clean

setup:
	python3 -m venv $(VENV)
	$(PIP) install --upgrade pip
	$(PIP) install -r requirements.txt

run:
	@test -n "$(q)" || { echo "kullanim: make run q=\"kelime\" [LIMIT=5] [AI=1]"; exit 1; }
	$(PY) main.py "$(q)" --limit $(LIMIT) $(AI_FLAG)

clean:
	rm -rf $(VENV) **/__pycache__ __pycache__
