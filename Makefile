# Device-specific venv path (Windows -> Scripts, otherwise -> bin)
ifeq ($(OS),Windows_NT)
	PY := venv/Scripts/python.exe
	PIP := venv/Scripts/python.exe -m pip
else
	PY := venv/bin/python
	PIP := venv/bin/pip
endif

# Parameters (override: make run q="bitcoin" LIMIT=5 TOPICS=10)
q ?=
LIMIT ?= 10
TOPICS ?= 10

.PHONY: setup login run run-raw clean

setup:
	python3 -m venv venv
	$(PIP) install --upgrade pip
	$(PIP) install -r requirements.txt
	$(PY) -m playwright install chromium

# Bir kerelik Reddit girisi (cookie kalici profile kaydedilir)
login:
	$(PY) -m src.login

run:
	@test -n "$(q)" || { echo "usage: make run q=\"keyword\" [LIMIT=5] [TOPICS=10]"; exit 1; }
	$(PY) main.py "$(q)" --limit $(LIMIT) --topics $(TOPICS)

# OpenAI'siz: sadece Reddit postlarini ceker (topic uretmez). /generate-blog ile ayni mantik.
run-raw:
	@test -n "$(q)" || { echo "usage: make run-raw q=\"keyword\" [LIMIT=10]"; exit 1; }
	$(PY) main.py "$(q)" --limit $(LIMIT) --raw

clean:
	rm -rf venv **/__pycache__ __pycache__
