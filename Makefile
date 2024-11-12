.venv/bin/activate: requirements.txt
	python3 -m venv .venv
	.venv/bin/pip3 install -r requirements.txt

.venv/bin/hatch: .venv/bin/activate
	.venv/bin/pip3 install hatch hatch-requirements-txt

.venv/bin/ruff: .venv/bin/activate
	.venv/bin/pip3 install ruff

.venv/bin/mypy: .venv/bin/activate
	.venv/bin/pip3 install mypy

install: .venv/bin/hatch
	.venv/bin/pip3 install .

check: .venv/bin/ruff .venv/bin/mypy
	.venv/bin/ruff check
	.venv/bin/mypy aosp --check-untyped-def
	.venv/bin/ruff format --check

clean:
	find . -name .venv -prune -o -name __pycache__ | xargs rm -rf

.PHONY: install check clean 
