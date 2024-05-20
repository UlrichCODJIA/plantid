from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from sqlalchemy.dialects.postgresql import JSONB
import datetime

db = SQLAlchemy()


class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    first_name = db.Column(db.String(50))
    last_name = db.Column(db.String(50))
    language_preference = db.Column(db.String(20), default="English")
    voice_preference = db.Column(db.String(50))  # Store voice ID for text-to-speech
    image_generation_style = db.Column(db.String(50))  # Store style preference
    registration_date = db.Column(db.DateTime, default=datetime.datetime.utcnow)
    refresh_token = db.Column(db.String(255))

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def __repr__(self):
        return f"<User {self.username}>"


class Conversation(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    timestamp = db.Column(db.DateTime, default=db.func.now())
    input_text = db.Column(db.Text)
    response_text = db.Column(db.Text)
    input_language = db.Column(db.String(20))
    output_language = db.Column(db.String(20))
    audio_data = db.Column(db.LargeBinary)  # Optional: Store audio data
    image_data = db.Column(db.LargeBinary)  # Optional: Store generated images
    metadata = db.Column(JSONB)
    dialogue_state = db.Column(db.String(50), default="start")

    user = db.relationship("User", backref=db.backref("conversations", lazy=True))

    def __repr__(self):
        return f"<Conversation {self.id} for User {self.user_id}>"
