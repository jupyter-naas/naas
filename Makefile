run:
	docker-compose up

sh:
	docker-compose exec naas /bin/bash

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

fmt:
	docker-compose exec naas /bin/bash -c 'pip3 install black==22.6.0 && black /home/ftp/naas/naas'

lint:
	docker-compose exec naas /bin/bash -c 'flake8 /home/ftp/naas/naas'

test:
	docker-compose exec naas /bin/bash -c 'cd /home/ftp/naas/ && pytest tests'

dep-update:
	echo "Updating 'naas' dependencies."
	docker-compose exec naas pip install -e '/home/ftp/naas[dev]'
	echo "Updating 'drivers' dependencies."
	docker-compose exec naas pip install -e '/home/ftp/drivers'

extension-watch:
	docker-compose exec naas /bin/bash -c 'cd /home/ftp/naas/extensions/naasai && jlpm watch'