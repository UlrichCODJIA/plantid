import logging
from flask import Flask
import redis
from logger import configure_logger
from app.utils.utils import retry_on_exception

logger = configure_logger(log_level=logging.DEBUG, log_file="logs/app.log")


class RedisManager:
    def __init__(self):
        self.redis_client = None

    @retry_on_exception(
        retries=3,
        delay=5,
        exceptions=(redis.exceptions.ConnectionError, redis.exceptions.TimeoutError),
    )
    def init_app(self, app: Flask):
        client = redis.Redis.from_url(app.config["REDIS_URL"])
        client.ping()

        if not client:
            logger.warning(
                "Falling back to filesystem sessions due to Redis connection issues."
            )
            app.config["SESSION_TYPE"] = "filesystem"
        else:
            app.config["SESSION_TYPE"] = "redis"
            app.config["SESSION_REDIS"] = client
        self.redis_client = client
        app.extensions["redis"] = self.redis_client

    def get_redis_client(self):
        if self.redis_client is None:
            raise RuntimeError("Redis client has not been initialized.")
        return self.redis_client
