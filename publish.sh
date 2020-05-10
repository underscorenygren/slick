#!/bin/bash
DOCKER_USERNAME=underscorenygren
DOCKER_NAME=slick
ACCOUNT_ID=$(aws sts get-caller-identity | jq .Account -r)
REGION=us-east-1
NAME=scraping
TAG=$ACCOUNT_ID.dkr.ecr.$REGION.amazonaws.com/$NAME

docker tag $DOCKER_USERNAME/$DOCKER_NAME:latest $TAG

eval $(aws ecr get-login --no-include-email)
docker push $TAG
