DEV_COMPOSE  = docker compose -f docker-compose.yml -f docker-compose.dev.yml
PROD_COMPOSE = docker compose -f docker-compose.yml -f docker-compose.prod.yml

.PHONY: dev dev-down prod prod-down migrate makemigration logs ps

dev:
	$(DEV_COMPOSE) up -d

dev-down:
	$(DEV_COMPOSE) down

prod:
	$(PROD_COMPOSE) up -d

prod-down:
	$(PROD_COMPOSE) down

migrate:
	$(DEV_COMPOSE) exec backend alembic upgrade head

makemigration:
	$(DEV_COMPOSE) exec backend alembic revision --autogenerate -m "$(msg)"

logs:
	$(DEV_COMPOSE) logs -f $(service)

ps:
	$(DEV_COMPOSE) ps
