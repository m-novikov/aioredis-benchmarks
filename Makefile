SHELL=/bin/bash
ROOT_DIR:=$(shell dirname $(realpath $(firstword $(MAKEFILE_LIST))))

REDIS_URL ?= redis://localhost:6379/
NUM_ITERATIONS ?= 10000
MAX_CONNECTIONS ?= 64

submodules:
	git submodule update --init --recursive

setup-env:
	python -m venv venv
	. venv/bin/activate
	python -m pip install -r requirements.txt

benchmark:
	@. venv/bin/activate
	@python -m aioredis_benchmarks.baseline
	@PYTHONPATH="$(ROOT_DIR)/vendor/aioredis-py-1.3" python -m aioredis_benchmarks.aioredis1
	@PYTHONPATH="$(ROOT_DIR)/vendor/aioredis-py-master" python -m aioredis_benchmarks.aioredis2
	@PYTHONPATH="$(ROOT_DIR)/vendor/aioredis-py-asyncio-protocol" python -m aioredis_benchmarks.aioredis2_proto
