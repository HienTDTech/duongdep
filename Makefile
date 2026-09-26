.PHONY: help install test lint precompute api route clean

BBOX ?= 20.996,105.827,21.004,105.836
GRAPH ?= data/test_area.json

help:
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN{FS=":.*?## "}{printf "  %-12s %s\n", $$1, $$2}'

install: ## cài package + deps api/dev
	pip install -e ".[api,dev]"

test: ## chạy test
	PYTHONPATH=src python -m pytest -q tests/

lint: ## ruff
	ruff check src tests

precompute: ## tải OSM vùng nhỏ + precompute graph
	PYTHONPATH=src python -m duongdep.cli precompute --source osm-api --bbox $(BBOX) --out $(GRAPH)

api: ## chạy webapp
	DUONGDEP_GRAPH=$(GRAPH) PYTHONPATH=src uvicorn duongdep.api.app:app --reload

route: ## ví dụ route trong graph đã precompute
	PYTHONPATH=src python -m duongdep.cli route --graph $(GRAPH) \
		--from 20.9962,105.8363 --to 20.9977,105.8230 --gmaps

clean: ## xoá data sinh ra
	rm -rf data/*.json data/*.db .pytest_cache
