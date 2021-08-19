../drivers:
	git clone https://github.com/jupyter-naas/drivers.git ../drivers

../awesome-notebooks:
	git clone https://github.com/jupyter-naas/awesome-notebooks.git ../awesome-notebooks

np: ../drivers ../awesome-notebooks

naas-build:
	docker-compose down
	docker-compose build

naas-run: np
	docker-compose up

naas-run-bg: np
	docker-compose up -d

naas-stop:
	docker-compose stop

naas-down:
	docker-compose down

naas-logs:
	docker-compose logs -f

