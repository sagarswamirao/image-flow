VERSION=v7
DOCKERUSER=pavan1820

build:
	docker build -f Dockerfile -t image-processor .

push:
	docker tag image-processor $(DOCKERUSER)/image-processor:$(VERSION)
	docker push $(DOCKERUSER)/image-processor:$(VERSION)
	docker tag image-processor $(DOCKERUSER)/image-processor:latest
	docker push $(DOCKERUSER)/image-processor:latest