from flask_sqlalchemy import SQLAlchemy
from flask_jwt_extended import JWTManager
from flask_session import Session

db = SQLAlchemy()
jwt = JWTManager()
session = Session()
