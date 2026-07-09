# Makefile raiz do monorepo: delega qualidade aos servicos e orquestra o compose.

SERVICES := services/auth services/vendas

.PHONY: install quality ci test up down logs

install:
	for s in $(SERVICES); do $(MAKE) -C $$s install || exit 1; done

quality:
	for s in $(SERVICES); do $(MAKE) -C $$s quality || exit 1; done

ci:
	for s in $(SERVICES); do $(MAKE) -C $$s ci || exit 1; done

test:
	for s in $(SERVICES); do $(MAKE) -C $$s test || exit 1; done

# --- Stack local (docker compose) --------------------------------------------
up:
	docker compose up -d --build

down:
	docker compose down -v

logs:
	docker compose logs -f vendas auth
