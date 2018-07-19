.PHONY: test clean


test: .venv
	.venv/bin/tox


clean:
	rm -rf .venv/ .eggs/ .tox/ .pytest_cache/ *.egg-info/ dist/


.venv:
	"$(shell which python3)" -m venv .venv
	.venv/bin/pip install --upgrade pip setuptools tox  # because of Jenkins
