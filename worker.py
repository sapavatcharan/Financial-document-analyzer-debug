import os

from redis import Redis
from rq import Connection, Queue, Worker


def get_redis_connection() -> Redis:
    redis_url = os.getenv("REDIS_URL", "redis://localhost:6379/0")
    return Redis.from_url(redis_url)


def main() -> None:
    listen = ["analysis"]
    conn = get_redis_connection()

    with Connection(conn):
        queues = [Queue(name) for name in listen]
        worker = Worker(queues)
        worker.work()


if __name__ == "__main__":
    main()

