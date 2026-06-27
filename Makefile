build:
	docker compose -f infra/docker-compose.yml up --build -d

up:
	docker compose -f infra/docker-compose.yml up -d

down:
	docker compose -f infra/docker-compose.yml down

restart:
	docker compose -f infra/docker-compose.yml down
	docker compose -f infra/docker-compose.yml up -d

logs:
	docker compose -f infra/docker-compose.yml logs -f

ps:
	docker compose -f infra/docker-compose.yml ps

clean:
	docker compose -f infra/docker-compose.yml down -v
	docker system prune -f