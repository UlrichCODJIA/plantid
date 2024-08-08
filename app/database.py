from mongoengine import connect


def initialize_db(app):
    db_name = app.config["MONGODB_DB"]
    db_host = app.config["MONGODB_HOST"]
    db_port = int(app.config["MONGODB_PORT"])
    db_username = app.config["MONGODB_USERNAME"]
    db_password = app.config["MONGODB_PASSWORD"]
    connect(
        host=f"mongodb+srv://{db_username}:{db_password}@{db_host}/{db_name}?retryWrites=true&w=majority&appName=Cluster0"
    )
