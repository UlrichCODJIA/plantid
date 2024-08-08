import os
from dotenv import load_dotenv

load_dotenv()

from app import create_app
from app.metrics import start_metrics_server

if __name__ == "__main__":
    from argparse import ArgumentParser

    parser = ArgumentParser(description="PLANTID - A plant identification application")
    parser.add_argument(
        "--environment",
        type=str,
        default="production",
        choices=["development", "production"],
        help="Specify the app environment. Possible values: development, production."
        " Default is development.",
    )
    args = parser.parse_args()
    start_metrics_server(port=6000)
    app = create_app(args)
    app.run(port=os.environ.get("PORT", 5000))
