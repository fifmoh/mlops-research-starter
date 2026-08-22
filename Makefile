.PHONY: help setup check test smoke run docs demo clean clean-room reproduce compare-reproductions api-smoke package contract-smoke
PY := uv run --python 3.11

help:
	@printf "%s\n" "setup check test smoke run docs demo clean clean-room reproduce compare-reproductions api-smoke package contract-smoke"
setup:
	uv sync --all-extras
check:
	uv lock --check
	$(PY) ruff format --check src tests
	$(PY) ruff check src tests
	$(PY) mypy src
test:
	$(PY) pytest
smoke:
	$(PY) python -m researchops.cli smoke
run:
	$(PY) python -m researchops
docs:
	$(PY) python -m researchops.cli docs
demo:
	$(PY) python -m researchops.cli demo
clean:
	rm -rf .pytest_cache .mypy_cache .ruff_cache build dist
clean-room:
	$(PY) python -m researchops.cli smoke

reproduce:
	$(PY) python -m researchops.cli reproduce
compare-reproductions:
	$(PY) python -m researchops.cli reproduce
api-smoke:
	$(PY) python -c "from researchops.api import app; assert app"
package:
	$(PY) python -m researchops.cli package
contract-smoke:
	$(PY) python -c "import researchops; assert researchops.__version__ == '0.1.0'"
