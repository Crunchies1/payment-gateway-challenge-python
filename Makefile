.PHONY: install
install:
	@poetry install 

.PHONY: run
run:
	@poetry run python main.py

.PHONY: test
test: 
	@poetry run python -m pytest -vv

.PHONY: test-integration
test-integration:
	@poetry run python -m pytest tests/integration/ -vv

.PHONY: test-unit
test-unit:
	@poetry run python -m pytest tests/unit/ -vv