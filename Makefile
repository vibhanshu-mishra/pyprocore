.PHONY: test coverage examples-check lint format typecheck clean

PYTHON ?= python3

test:
	$(PYTHON) -m unittest discover -s tests

coverage:
	$(PYTHON) -m coverage erase
	$(PYTHON) -m coverage run -m unittest discover -s tests
	$(PYTHON) -m coverage report

examples-check:
	$(PYTHON) scripts/check_examples.py

lint:
	$(PYTHON) -m black --check pyprocore tests
	$(PYTHON) -m isort --check-only pyprocore tests
	$(PYTHON) -m flake8 pyprocore tests

format:
	$(PYTHON) -m isort pyprocore tests
	$(PYTHON) -m black pyprocore tests

typecheck:
	$(PYTHON) -m mypy pyprocore

clean:
	find . -name "__pycache__" -type d -prune -exec rm -rf {} +
	find . -name "*.pyc" -type f -delete
	rm -rf .coverage htmlcov .mypy_cache .pytest_cache build dist *.egg-info logs
