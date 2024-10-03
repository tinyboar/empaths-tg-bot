.PHONY: build up down restart logs

build:
	docker-compose build

up:
	docker-compose up -d

down:
	docker-compose down

restart:
	docker-compose down && docker-compose up -d

logs:
	docker-compose logs -f

init-db:
	docker-compose run --rm telegram_bot python -c "from database import init_db; init_db()"

db:
	docker-compose exec telegram_bot sqlite3 /app/empaths.db
