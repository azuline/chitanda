cov:
	pytest --cov-report term-missing --cov-branch --cov chitanda tests/

htmlcov:
	coverage html
	xdg-open htmlcov/index.html

lint:
	black -S -t py37 -l 79 chitanda tests
	isort -rc chitanda tests
	flake8 chitanda tests

tests:
	pytest tests/
	black -S -t py37 -l 79 --check chitanda tests
	isort -rc -c chitanda tests
	flake8 chitanda tests

docs:
	sphinx-build -M html docs docs/_build

.PHONY: cov htmlcov lint tests docs
