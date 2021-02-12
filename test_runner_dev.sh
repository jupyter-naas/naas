docker rm $(docker ps -aq --filter name=naas_test)
docker run \
    --name naas_test \
    -e ALLOWED_IFRAME='' \
    -e JUPYTERHUB_URL='127.0.0.1:8888' \
    -p 8888:8888 \
    -p 5000:5000 \
    -v `pwd`:/home/ftp/naas \
    -v ~/.ssh:/home/ftp/.ssh \
    naas_test
