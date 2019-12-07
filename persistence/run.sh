#!/bin/bash
# Run database server for skrate persistence layer

docker run --network bridge -p 5432:5432 -e POSTGRES_PASSWORD=postgress_password \
	--name skrate-persistence skrate_persistence:latest

# Kill it when done
docker container rm skrate-persistence
