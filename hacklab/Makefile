.PHONY: up down stop reset ps logs

up:
	docker compose up --build

start:
	docker compose up -d

stop:
	docker compose stop

down:
	docker compose down

reset:
	docker compose down -v
	docker compose up --build

ps:
	docker compose ps

logs:
	docker compose logs -f
