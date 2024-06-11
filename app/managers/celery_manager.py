# celery_manager.py

from celery import Celery, Task
from flask import Flask


class CeleryManager:
    def __init__(self):
        self.celery_app = None

    def init_app(self, app: Flask):
        class FlaskTask(Task):
            def __call__(self, *args: object, **kwargs: object) -> object:
                with app.app_context():
                    return self.run(*args, **kwargs)

        self.celery_app = Celery(app.name, task_cls=FlaskTask)
        self.celery_app.config_from_object(app.config["CELERY"])
        self.celery_app.set_default()
        app.extensions["celery"] = self.celery_app

    def get_celery_app(self):
        if self.celery_app is None:
            raise RuntimeError("Celery app has not been initialized.")
        return self.celery_app
