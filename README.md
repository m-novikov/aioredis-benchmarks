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
simple_async: 1500 tasks with blocking pool with 64 connections: 0.049057960510253906s
aioredis1: 1500 tasks with blocking pool with 64 connections: 0.0681612491607666s
aioredis2: 1500 tasks with blocking pool with 64 connections: 0.3374614715576172s
```
