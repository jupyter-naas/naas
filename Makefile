run: np
	docker-compose up

../drivers:
	git clone https://github.com/jupyter-naas/drivers.git ../drivers

../awesome-notebooks:
	git clone https://github.com/jupyter-naas/awesome-notebooks.git ../awesome-notebooks

np: ../drivers ../awesome-notebooks

build:
	docker-compose down
	docker-compose build

run-bg: np
	docker-compose up -d

stop:
	docker-compose stop

down:
	docker-compose down

logs:
	docker-compose logs -f

