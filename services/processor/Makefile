image := ynput/ayon-openpype-import:latest

build:
	docker build -t $(image)  . 

clean:
	docker rmi $(image)

dist: build
	docker push $(image)

dev:
	docker run --rm -ti \
		-v $(CURDIR):/service \
		--hostname op3import \
		--env AYON_API_KEY=b00b567890123456789012345678iee5 \
		--env AYON_SERVER_URL="http://172.25.0.1:5000" \
		--env AYON_ADDON_NAME=openpype_import \
		--env AYON_ADDON_VERSION=1.0.0 \
		$(image) python -m processor
