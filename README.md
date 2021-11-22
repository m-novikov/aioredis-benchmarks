# Benchmarking aioredis 2.0

## To run benchmarks

```bash
# To pull relevant aioredis versions
make submodules
# Setup aioredis dependencies
make setup-env
# Run benchmarks
make benchmark
```

It's possible to set envoriment variables before running make to customize benchmark:
e.g.
```
REDIS_URL="redis://localhost:6379/" NUM_ITERATIONS=1500 MAX_CONNECTIONS=1 make benchmark
```

Results with locally running redis:

```
simple_async: 1500 tasks with blocking pool with 64 connections: 0.048108816146850586s
aioredis1: 1500 tasks with blocking pool with 64 connections: 0.07063984870910645s
aioredis2: 1500 tasks with blocking pool with 64 connections: 0.34310436248779297s
aioredis2_proto: 1500 tasks with blocking pool with *1* connection: 0.0847783088684082s
```

Results with remote running redis:

```
simple_async: 10000 tasks with blocking pool with 64 connections: 0.364227294921875s
aioredis1: 10000 tasks with blocking pool with 64 connections: 0.42733216285705566s
aioredis2: 10000 tasks with blocking pool with 64 connections: 16.949565649032593s
aioredis2_proto: 10000 tasks with blocking pool with *1* connection: 0.5196411609649658s
```
