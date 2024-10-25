import logging

import redis
from app.utils.utils import retry_on_exception
from flask import Flask
from flask_jwt_extended import get_jwt_identity, verify_jwt_in_request
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from logger import configure_logger

logger = configure_logger(log_level=logging.DEBUG, log_file="logs/app.log")


class RedisManager:
    def __init__(self):
        self.redis_client = None
        self.limiter = None

    @retry_on_exception(
        retries=3,
        delay=5,
        exceptions=(redis.exceptions.ConnectionError, redis.exceptions.TimeoutError),
    )
    def init_app(self, app: Flask, init_limiter=False):
        client = redis.Redis.from_url(app.config["REDIS_URL"])
        client.ping()

        if not client:
            logger.warning("Falling back to filesystem sessions due to Redis connection issues.")
            app.config["SESSION_TYPE"] = "filesystem"
        else:
            app.config["SESSION_TYPE"] = "redis"
            app.config["SESSION_REDIS"] = client

        self.redis_client = client
        app.extensions["redis"] = self.redis_client

        if init_limiter:
            self._init_limiter(app)

    def _init_limiter(self, app):
        try:
            default_limits = app.config.get("RATELIMIT_DEFAULT", [])

            self.limiter = Limiter(
                app=app,
                key_func=lambda: (get_jwt_identity() if verify_jwt_in_request(optional=True) else get_remote_address()),
                default_limits=default_limits,
                storage_uri=app.config["REDIS_URL"],
                storage_options=app.config.get("RATELIMIT_STORAGE_OPTIONS", {}),
                strategy=app.config.get("RATELIMIT_STRATEGY", "moving-window"),
            )
            logger.info("Flask-Limiter initialized with Redis storage")
        except Exception as e:
            logger.error(f"Failed to initialize Flask-Limiter: {str(e)}")
            raise

    def init_limiter(self, app):
        """
        Manually initialize limiter after Redis manager has been set up
        """
        if self.redis_client is None:
            raise RuntimeError("Redis client must be initialized before limiter")
        self._init_limiter(app)

    def get_redis_client(self):
        if self.redis_client is None:
            raise RuntimeError("Redis client has not been initialized.")
        return self.redis_client

    def get_limiter(self):
        if self.limiter is None:
            raise RuntimeError("Limiter has not been initialized. Call init_limiter() first.")
        return self.limiter
