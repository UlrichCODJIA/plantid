from argparse import ArgumentParser, Namespace

from dotenv import load_dotenv

load_dotenv()

from app import create_app
from app.extensions import celery_manager

if __name__ == "__main__":
    parser = ArgumentParser(description="PLANTID - Celery worker")
    parser.add_argument(
        "--loglevel",
        type=str,
        default="info",
        choices=["debug", "info", "warning", "error", "critical"],
        help="Specify the log level for the Celery worker. Default is info.",
    )
    args = parser.parse_args()

    app_args = Namespace(environment="make_celery")

    app = create_app(app_args)

    celery = celery_manager.get_celery_app()

    celery.worker_main(["worker", f"--loglevel={args.loglevel}"])
