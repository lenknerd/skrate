#!/bin/bash
# Build and run database server for skrate persistence layer

SERVER_TAG="skrate_persistence"
CONTAINER_NAME="skrate-persistence"

# Folder where this script resides
SDIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"

docker build -t ${SERVER_TAG} .

docker run --network bridge -p 5432:5432 -e POSTGRES_PASSWORD=postgres_password \
	-e PGDATA=${SDIR}/postgres_data --name ${CONTAINER_NAME} -d ${SERVER_TAG}:latest
