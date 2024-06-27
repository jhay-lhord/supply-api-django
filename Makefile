.PHONY: activate
activate:
	poetry shell

.PHONY: runserver
runserver:
	poetry run python3 manage.py runserver

.PHONY: migrations
migrations:
	poetry run python3 manage.py makemigrations

.PHONY: migrate
migrate:
	poetry run python3 manage.py migrate

.PHONY: superuser
superuser:
	poetry run python3 manage.py createsuperuser

.PHONY: lint
lint:
	poetry run pre-commit run --all-files
