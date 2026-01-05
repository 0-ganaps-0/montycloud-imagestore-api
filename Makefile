
SHELL := /bin/bash
REGION ?= us-east-1

up:
	docker compose up -d

down:
	docker compose down -v

build_zip:
	cd src && zip -r ../lambda.zip . >/dev/null

deploy: build_zip
	bash scripts/deploy.sh

destroy:
	bash scripts/teardown.sh

# convenience
apis:
	awslocal apigateway get-rest-apis

logs:
	awslocal logs describe-log-groups

test:
    PYTHONPATH=./ pytest -q

.PHONY: up down build_zip deploy destroy apis logs
