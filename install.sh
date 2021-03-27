#!/usr/bin/env bash
BUILD="YES"
SUPP="NO"
N_ENV="dev"
RUN="NO"
TOKEN="test"
for i in "$@"
do

case $i in
    -ro|--run-only)
    BUILD="NO"
    RUN="YES"
    shift # past argument=value
    ;;
    -s|--supp)
    SUPP="YES"
    shift # past argument=value
    ;;
    -p|--prod)
    N_ENV="prod"
    shift # past argument=value
    ;;
    -r|--run)
    RUN="YES"
    shift # past argument=value
    ;;
    -t=*|--token=*)
    TOKEN="${i#*=}"
    shift # past argument=value
    ;;
    *)
    echo "UNRECONIZED ARGUMENT"
    exit
    ;;
esac
done

if [[ $BUILD == "YES" ]]; then
    docker pull jupyternaas/singleuser:latest
    docker build -f Dockerfile.$N_ENV --build-arg INSTALL_SUPP=$SUPP -t naas_$N_ENV .
    echo "Build done"
fi


if [[ $RUN == "YES" ]]; then
    echo "============================= RUN Naas ============================="
    docker rm $(docker ps -aq --filter name=naas_$N_ENV)
    docker run \
        --name naas_$N_ENV \
        -e ALLOWED_IFRAME='' \
        -e JUPYTER_ENABLE_LAB='yes' \
        -e JUPYTER_TOKEN="$TOKEN" \
        -e JUPYTERHUB_URL='http://127.0.0.1:8888' \
        -p 8888:8888 \
        -p 5000:5000 \
        -v $(pwd):/home/ftp/naas \
        -v ~/.ssh:/home/ftp/.ssh \
        naas_$N_ENV
fi