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

dep-update:
	echo "Updating 'naas' dependencies."
	docker-compose exec naas pip install -e '/home/ftp/naas[dev]'
	echo "Updating 'drivers' dependencies."
	docker-compose exec naas pip install -e '/home/ftp/drivers'

extension-watch:
	docker-compose exec naas /bin/bash -c 'cd /home/ftp/naas/extensions/naasai && jlpm watch'