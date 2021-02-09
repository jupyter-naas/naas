docker build -f Dockerfile -t naas_prod .
docker run \
    --name naas_prod \
    -p 8888:8888 \
    -p 5000:5000 \
    naas_prod
