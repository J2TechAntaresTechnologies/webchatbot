.PHONY: install-base install-dev install-rag test context-show context-save

PYTHON ?= python
PIP ?= pip

ifneq (,$(wildcard bin/python))
PYTHON := ./bin/python
PIP := ./bin/pip
endif

install-base:
	$(PYTHON) -m pip install -r requirements.txt

install-dev:
	$(PYTHON) -m pip install -r requirements/dev.txt

install-rag:
	$(PYTHON) -m pip install -r requirements/rag.txt

test:
	$(PYTHON) -m pytest

context-show:
	$(PYTHON) scripts/context_manager.py show --brief

context-save:
	$(PYTHON) scripts/context_manager.py save --auto
