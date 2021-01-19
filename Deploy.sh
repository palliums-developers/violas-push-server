#!/bin/bash

sudo docker stop violas-push-service
sudo docker rm violas-push-service
sudo docker image rm violas-push-service
sudo docker image build --no-cache -t violas-push-service .
sudo docker run --name=violas-push-service --network=host -d violas-push-service
