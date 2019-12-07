#!/bin/bash
# Build and run database server for skrate persistence layer

SERVER_TAG="skrate_persistence"
CONTAINER_NAME="skrate-persistence"

docker build -t ${SERVER_TAG} .

docker run --network bridge -p 5432:5432 -e POSTGRES_PASSWORD=postgress_password \
	--name ${CONTAINER_NAME} ${SERVER_TAG}:latest

# Kill it when done
docker container rm ${CONTAINER_NAME}
