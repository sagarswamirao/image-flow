VERSION=v5
DOCKERUSER=pavan1820

build:
	docker build -f Dockerfile -t image-handler .

push:
	docker tag image-handler $(DOCKERUSER)/image-handler:$(VERSION)
	docker push $(DOCKERUSER)/image-handler:$(VERSION)
	docker tag image-handler $(DOCKERUSER)/image-handler:latest
	docker push $(DOCKERUSER)/image-handler:latest