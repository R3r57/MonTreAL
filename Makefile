#Needs the following environment variables:
#	NAME - the application name in lowercase
#	ARCH - the architecture type, e.g 'amd64'
#	VERSION - the version
#	DOCKER_USER - the docker username
default: all
all: build

build:
	docker run --rm --privileged multiarch/qemu-user-static:register --reset
	curl -sL https://github.com/multiarch/qemu-user-static/releases/download/v2.9.1/qemu-arm-static.tar.gz | tar -xzC .
	docker build --pull --cache-from ${DOCKER_USER}/${NAME}:${VERSION}-${ARCH} --build-arg VCS_URL=${REPO_URL} --build-arg BUILD_DATE=`date -u +"%Y-%m-%dT%H:%M:%SZ"` --build-arg VCS_REF=${TRAVIS_COMMIT} --build-arg VERSION=${VERSION} -t "${DOCKER_USER}/${NAME}:${VERSION}-${ARCH}" -f Dockerfile.${DOTARCH} .
	$(MAKE) clean

clean:
	rm -rf qemu-arm-static

ifndef NAME
	$(error NAME not defined)
endif
ifndef ARCH
	$(error ARCH not defined)
endif
ifndef VERSION
	$(error VERSION not defined)
endif
ifndef DOCKER_USER
	$(error DOCKER_USER not defined)
endif