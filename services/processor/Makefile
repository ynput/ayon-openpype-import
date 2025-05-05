image := ynput/ayon-openpype-import:0.3.0

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
		--env AYON_API_KEY=veryinsecurapikey \
		--env AYON_SERVER_URL="http://192.168.5.141:5000" \
		--env AYON_ADDON_NAME=openpype_import \
		--env AYON_ADDON_VERSION=0.3.0 \
		$(image) python -m processor
