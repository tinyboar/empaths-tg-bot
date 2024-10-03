.PHONY: build up down restart logs clean-rebuild up-logs

build:
	docker-compose build

up:
	@if [ "$(l)" = "true" ]; then \
		make up-logs; \
	else \
		docker-compose up -d; \
	fi

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

clean-rebuild:
	docker-compose down -v --rmi all --remove-orphans
	docker-compose build
	docker-compose up -d
	docker-compose run --rm telegram_bot python -c "from database import init_db; init_db()"


up-logs:
	docker-compose up && docker-compose logs -f