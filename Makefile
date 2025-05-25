test:
	uv run pytest tests

docker-up:
	docker compose up -d

docker-down:
	docker compose down

s3-exporter:
	uv run scripts/s3_exporter.py