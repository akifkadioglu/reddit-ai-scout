# Device-specific venv path (Windows -> Scripts, otherwise -> bin)
ifeq ($(OS),Windows_NT)
	PY := venv/Scripts/python.exe
	PIP := venv/Scripts/python.exe -m pip
else
	PY := venv/bin/python
	PIP := venv/bin/pip
endif

# Parameters (override: make run q="bitcoin" LIMIT=5 AI=1)
q ?=
LIMIT ?= 10
AI ?=
AI_FLAG := $(if $(AI),--ai,)

.PHONY: setup run clean

setup:
	python3 -m venv venv
	$(PIP) install --upgrade pip
	$(PIP) install -r requirements.txt
	$(PY) -m playwright install chromium

run:
	@test -n "$(q)" || { echo "usage: make run q=\"keyword\" [LIMIT=5] [AI=1]"; exit 1; }
	$(PY) main.py "$(q)" --limit $(LIMIT) $(AI_FLAG)

clean:
	rm -rf venv **/__pycache__ __pycache__
