image := ynput/ayon-openpype-import:1.0.0

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
		--env AY_API_KEY=b00b567890123456789012345678iee5 \
		--env AY_SERVER_URL="http://172.18.0.1:5000" \
		--env AY_ADDON_NAME=openpype_import \
		--env AY_ADDON_VERSION=1.0.0 \
		$(image) python -m processor
