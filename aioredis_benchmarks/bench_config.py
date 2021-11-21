import os

max_conn = int(os.environ.get('MAX_CONNECTIONS', 64))
num_iterations = os.environ.get('NUM_ITERATIONS', 10000)
url = os.environ.get('REDIS_URL', 'redis://localhost:6379')
