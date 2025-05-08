#!/bin/bash

LOG_FILE="linter.log"
touch $LOG_FILE

docker pull github/super-linter:latest

exec > >(tee $LOG_FILE) 2>&1
docker run \
    -e RUN_LOCAL=true \
    -e VALIDATE_PYTHON=true \
    -v ${PWD}:/tmp/lint \
    github/super-linter
