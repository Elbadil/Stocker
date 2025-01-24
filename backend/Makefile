# Variables
PYTHON = python3
MANAGE = $(PYTHON) manage.py

.PHONY: clean run shell migrations migrate createsuperuser test help

# Targets
run:
	$(MANAGE) runserver

shell:
	$(MANAGE) shell

migrations:
	$(MANAGE) makemigrations

migrate:
	$(MANAGE) migrate

createsuperuser:
	$(MANAGE) createsuperuser

test:
	pytest --reuse-db

# Help command
help:
	@echo "Available commands:"
	@echo "  make shell           - Open Django shell"
	@echo "  make migrations      - Create new migrations"
	@echo "  make migrate         - Apply migrations"
	@echo "  make run             - Start development server"
	@echo "  make test            - Run tests using pytest"
	@echo "  make createsuperuser - Create a superuser"
