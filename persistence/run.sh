#!/bin/bash
# Build and run database server for skrate persistence layer

SERVER_TAG="skrate_persistence"
CONTAINER_NAME="skrate-persistence"
DATA_LOC_IN_CONTAINER="/var/lib/postgresql/data/mounted_data_dir"

# Folder where this script resides
SDIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"

# Data directory for postgres
docker volume create skrate-vol

docker build -t ${SERVER_TAG} .

docker run --network bridge -p 5432:5432 -e POSTGRES_PASSWORD=postgres_password \
	-e PGDATA=${DATA_LOC_IN_CONTAINER} \
   	--mount source=skrate-vol,target=${DATA_LOC_IN_CONTAINER} --name ${CONTAINER_NAME} \
	-d ${SERVER_TAG}:latest
