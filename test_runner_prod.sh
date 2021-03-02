docker build -f Dockerfile -t naas_prod .
docker run \
    --name naas_prod \
    -e JUPYTER_ENABLE_LAB='yes' \
    -e JUPYTER_TOKEN='testnaas' \
    -p 8888:8888 \
    -p 5000:5000 \
    naas_prod
