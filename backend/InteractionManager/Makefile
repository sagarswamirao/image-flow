VERSION=v4
DOCKERUSER=pavan1820

build:
	docker build -f Dockerfile -t interaction-manager .

push:
	docker tag interaction-manager $(DOCKERUSER)/interaction-manager:$(VERSION)
	docker push $(DOCKERUSER)/interaction-manager:$(VERSION)
	docker tag interaction-manager $(DOCKERUSER)/interaction-manager:latest
	docker push $(DOCKERUSER)/interaction-manager:latest