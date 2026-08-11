.PHONY: install test lint validate up down logs smoke generate package
install:
	python -m pip install -e .

test:
	PYTHONPATH=packages python -m unittest discover -s tests -v

lint:
	python -m compileall -q packages apps ml monitoring pipelines tests

validate: lint test
	python scripts/validate_repo.py
	@if command -v docker >/dev/null 2>&1; then docker compose config >/dev/null; else echo "docker not installed; compose validation skipped"; fi

up:
	docker compose up -d --build

down:
	docker compose down -v

logs:
	docker compose logs -f --tail=100

smoke:
	curl -fsS http://localhost:8000/health
	curl -fsS -X POST http://localhost:8000/v1/recommendations -H 'Content-Type: application/json' -d '{"user_id":"u-1001","top_k":3,"context":{"device":"web","hour":20}}'

generate:
	docker compose run --rm event-generator

package:
	cd .. && zip -qr EduRecOps.zip EduRecOps -x 'EduRecOps/.git/*' 'EduRecOps/**/__pycache__/*'
