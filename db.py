from redis import Redis
from rq import Queue

redis_conn = Redis()
q = Queue(connection=redis_conn)