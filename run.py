from app import create_app
from multilingual_webapp.app.extensions import db

if __name__ == "__main__":
    from argparse import ArgumentParser

    parser = ArgumentParser(description="PLANTID - A plant identification application")

    parser.add_argument(
        "--environment",
        type=str,
        default="development",
        choices=["development", "production"],
        help="Specify the app environment. Possible values: development, production."
        " Default is development.",
    )

    args = parser.parse_args()

    app = create_app(args)

    with app.app_context():
        db.create_all()
    app.run()
