.PHONY: test coverage examples-check smoke-documents smoke-drawings smoke-specifications smoke-photos lint format typecheck clean

PYTHON ?= python3

test:
	$(PYTHON) -m unittest discover -s tests

coverage:
	$(PYTHON) -m coverage erase
	$(PYTHON) -m coverage run -m unittest discover -s tests
	$(PYTHON) -m coverage report

examples-check:
	$(PYTHON) scripts/check_examples.py

smoke-documents:
	@if [ -z "$$PROCORE_PROJECT_ID" ]; then \
		echo "Documents smoke test needs PROCORE_PROJECT_ID."; \
		echo "Example: PROCORE_PROJECT_ID=352338 make smoke-documents"; \
		exit 1; \
	fi
	@args="--project $$PROCORE_PROJECT_ID"; \
	if [ -n "$$PROCORE_DOCUMENT_FOLDER_ID" ]; then args="$$args --folder $$PROCORE_DOCUMENT_FOLDER_ID"; fi; \
	if [ -n "$$PROCORE_COMPANY_ID" ]; then args="$$args --company-id $$PROCORE_COMPANY_ID"; fi; \
	PYTHONPATH=. $(PYTHON) scripts/smoke_documents.py $$args

smoke-drawings:
	@if [ -z "$$PROCORE_PROJECT_ID" ]; then \
		echo "Drawings smoke test needs PROCORE_PROJECT_ID."; \
		echo "Example: PROCORE_PROJECT_ID=352338 make smoke-drawings"; \
		exit 1; \
	fi
	@args="--project $$PROCORE_PROJECT_ID"; \
	if [ -n "$$PROCORE_DRAWING_AREA_ID" ]; then args="$$args --area $$PROCORE_DRAWING_AREA_ID"; fi; \
	if [ -n "$$PROCORE_DRAWING_ID" ]; then args="$$args --drawing $$PROCORE_DRAWING_ID"; fi; \
	if [ -n "$$PROCORE_COMPANY_ID" ]; then args="$$args --company-id $$PROCORE_COMPANY_ID"; fi; \
	PYTHONPATH=. $(PYTHON) scripts/smoke_drawings.py $$args

smoke-specifications:
	@if [ -z "$$PROCORE_PROJECT_ID" ]; then \
		echo "Specifications smoke test needs PROCORE_PROJECT_ID."; \
		echo "Example: PROCORE_PROJECT_ID=352338 make smoke-specifications"; \
		exit 1; \
	fi
	@args="--project $$PROCORE_PROJECT_ID"; \
	if [ -n "$$PROCORE_COMPANY_ID" ]; then args="$$args --company $$PROCORE_COMPANY_ID"; fi; \
	if [ -n "$$PROCORE_SPECIFICATION_SECTION_ID" ]; then args="$$args --section $$PROCORE_SPECIFICATION_SECTION_ID"; fi; \
	if [ -n "$$PROCORE_SPECIFICATION_REVISION_ID" ]; then args="$$args --revision $$PROCORE_SPECIFICATION_REVISION_ID"; fi; \
	PYTHONPATH=. $(PYTHON) scripts/smoke_specifications.py $$args

smoke-photos:
	@if [ -z "$$PROCORE_PROJECT_ID" ]; then \
		echo "Photos smoke test needs PROCORE_PROJECT_ID."; \
		echo "Example: PROCORE_PROJECT_ID=352338 make smoke-photos"; \
		exit 1; \
	fi
	@args="--project $$PROCORE_PROJECT_ID"; \
	if [ -n "$$PROCORE_COMPANY_ID" ]; then args="$$args --company $$PROCORE_COMPANY_ID"; fi; \
	if [ -n "$$PROCORE_PHOTO_ALBUM_ID" ]; then args="$$args --album $$PROCORE_PHOTO_ALBUM_ID"; fi; \
	if [ -n "$$PROCORE_PHOTO_ID" ]; then args="$$args --photo $$PROCORE_PHOTO_ID"; fi; \
	PYTHONPATH=. $(PYTHON) scripts/smoke_photos.py $$args

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
