lint:
	poetry run black .
	poetry run isort .
	poetry run flake8 .

tests:
	poetry run pytest --cov-report term-missing --cov-branch --cov=. tests/
	poetry run black --check .
	poetry run isort -c .
	poetry run flake8 .
	poetry run coverage html

docs:
	poetry run sphinx-build -M html docs docs/_build

setup.py:
	dephell deps convert --from pyproject.toml --to setup.py

.PHONY: lint tests docs setup.py
