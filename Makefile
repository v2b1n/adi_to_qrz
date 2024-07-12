PROJECT := adi_to_qrz

.PHONY: build run clean distrib

all: build test

build:
	docker build . -f Dockerfile -t $(PROJECT)
	docker tag $(PROJECT) $(PROJECT):latest
test:
	# run & test the code backed into the container
	docker run --entrypoint=/bin/bash -ti $(PROJECT):latest "/app/.tests/run.sh"


run:
	docker run $(PROJECT)


build-nc:
	docker build . -f Dockerfile -t $(PROJECT) --no-cache --pull
	docker tag $(PROJECT) $(PROJECT):latest

localtest:
	# run tests on the localcode
	docker run --entrypoint=/bin/bash -v $(PWD):/app -ti $(PROJECT):latest ".tests/run.sh"

shell:
	docker run --entrypoint=/bin/bash -ti $(PROJECT):latest

localshell:
	# start a shell & bind the local dir as /app
	docker run --entrypoint=/bin/bash -v $(PWD):/app -ti $(PROJECT):latest
