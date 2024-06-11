from mongoengine import connect


def initialize_db(app):
    db_name = app.config["MONGODB_DB"]
    db_host = app.config["MONGODB_HOST"]
    db_port = app.config["MONGODB_PORT"]
    db_username = app.config["MONGODB_USERNAME"]
    db_password = app.config["MONGODB_PASSWORD"]

    connect(
        db_name, host=db_host, port=db_port, username=db_username, password=db_password
    )
