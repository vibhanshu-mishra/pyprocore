.PHONY: test coverage lint format typecheck clean

PYTHON ?= .venv/bin/python

test:
	$(PYTHON) -m unittest discover -s tests

coverage:
	$(PYTHON) -m coverage erase
	$(PYTHON) -m coverage run -m unittest discover -s tests
	$(PYTHON) -m coverage report

lint:
	$(PYTHON) -m black --check app.py auth core models parser services tests
	$(PYTHON) -m isort --check-only app.py auth core models parser services tests
	$(PYTHON) -m flake8 app.py auth core models parser services tests

format:
	$(PYTHON) -m isort app.py auth core models parser services tests
	$(PYTHON) -m black app.py auth core models parser services tests

typecheck:
	$(PYTHON) -m mypy app.py auth core models parser services

clean:
	find . -name "__pycache__" -type d -prune -exec rm -rf {} +
	find . -name "*.pyc" -type f -delete
	rm -rf .coverage htmlcov .mypy_cache .pytest_cache build dist *.egg-info logs
