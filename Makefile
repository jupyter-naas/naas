run:
	docker-compose up

build:
	docker-compose down
	docker-compose build

run-bg:
	docker-compose up -d

stop:
	docker-compose stop

down:
	docker-compose down

logs:
	docker-compose logs -f

