PYTHON ?= python3
PY := .venv/bin/python
UV := .venv/bin/uv

.PHONY: setup setup-dev setup-inspect security lint format typecheck test run reproduce inspect docs build audit clean

setup:
	$(PYTHON) -m venv .venv
	$(PY) -m pip install --disable-pip-version-check --only-binary=:all: --require-hashes -r requirements-runtime.txt
	$(PY) -m pip install --disable-pip-version-check --no-index --no-build-isolation --no-deps -e .

setup-dev: setup
	$(UV) pip install --python $(PY) --require-hashes -r requirements-dev.txt
	$(PY) scripts/install_gitleaks.py
	$(PY) -m pre_commit install

setup-inspect:
	$(PYTHON) -m venv .venv-inspect
	$(UV) pip install --python .venv-inspect/bin/python --require-hashes -r requirements-inspect.txt

lint:
	.venv/bin/ruff check src tests scripts
	.venv/bin/black --check src tests scripts

format:
	.venv/bin/ruff check src tests scripts --fix
	.venv/bin/black src tests scripts

typecheck:
	.venv/bin/mypy --no-native-parser

test:
	.venv/bin/pytest --cov --cov-report=term-missing --cov-report=json:reports/local/coverage.json --junitxml=reports/local/tests.xml

run:
	$(PY) -m etl

reproduce:
	$(PY) scripts/reproduce.py
	$(PY) scripts/execute_notebook.py
	$(PY) scripts/check_reproduction.py

inspect:
	.venv-inspect/bin/python scripts/inspect_model.py --output reports/local/model
	$(PY) scripts/check_model.py reports/local/model

docs:
	$(PY) scripts/check_docs.py

build:
	$(PY) -m build --no-isolation

audit:
	.venv/bin/pip-audit --disable-pip --no-deps -r requirements-runtime.txt -r requirements-dev.txt

security:
	$(PY) scripts/install_gitleaks.py
	.tools/gitleaks git --redact --report-format=json --report-path=reports/local/history-secrets.json
	$(MAKE) audit

clean:
	rm -rf data/processed data/interim reports/local build dist .pytest_cache .mypy_cache .ruff_cache .coverage
	find src tests scripts -type d -name __pycache__ -prune -exec rm -rf {} +
