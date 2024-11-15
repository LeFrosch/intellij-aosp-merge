.venv/bin/activate: requirements.txt
	python3 -m venv .venv
	.venv/bin/pip3 install -r requirements.txt

.venv/bin/hatch: .venv/bin/activate
	.venv/bin/pip3 install hatch hatch-requirements-txt

install: .venv/bin/hatch
	.venv/bin/pip3 install .

clean:
	find . -name .venv -prune -o -name __pycache__ | xargs rm -rf

.PHONY: install clean 
