from argparse import Namespace
from dotenv import load_dotenv

load_dotenv()

from app import create_app
from app.extensions import celery_manager

args = Namespace(environment="make_celery")
flask_app = create_app(args)
celery_app = celery_manager.get_celery_app()
