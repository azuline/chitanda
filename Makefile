lint:
	black .
	isort .
	flake8 .

tests:
	pytest --cov-report term-missing --cov-branch --cov=. tests/
	black --check .
	isort -c .
	flake8 .
	coverage html

docs:
	sphinx-build -M html docs docs/_build

.PHONY: lint tests docs
