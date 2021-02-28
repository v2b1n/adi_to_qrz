PROJECT := adi_to_qrz

.PHONY: build run clean distrib

all: build test

build:
	docker build . -f Dockerfile -t $(PROJECT)
	docker tag $(PROJECT) $(PROJECT):latest

build-nc:
	docker build . -f Dockerfile -t $(PROJECT) --no-cache --pull
	docker tag $(PROJECT) $(PROJECT):latest

test:
	docker run -v $(PWD):/app -ti $(PROJECT):latest ".tests/run.sh"

run:
	docker run --entrypoint=/bin/bash -v $(PWD):/app -ti $(PROJECT):latest
