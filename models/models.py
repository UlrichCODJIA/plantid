from flask import current_app
from werkzeug.security import generate_password_hash, check_password_hash
from sqlalchemy.dialects.postgresql import JSONB
import datetime


class User(current_app.current_app.db.Model):
    id = current_app.current_app.db.Column(
        current_app.current_app.db.Integer, primary_key=True
    )
    username = current_app.db.Column(
        current_app.db.String(80), unique=True, nullable=False
    )
    password_hash = current_app.db.Column(current_app.db.String(128), nullable=False)
    email = current_app.db.Column(
        current_app.db.String(120), unique=True, nullable=False
    )
    first_name = current_app.db.Column(current_app.db.String(50))
    last_name = current_app.db.Column(current_app.db.String(50))
    language_preference = current_app.db.Column(
        current_app.db.String(20), default="English"
    )
    voice_preference = current_app.db.Column(
        current_app.db.String(50)
    )  # Store voice ID for text-to-speech
    image_generation_style = current_app.db.Column(
        current_app.db.String(50)
    )  # Store style preference
    registration_date = current_app.db.Column(
        current_app.db.DateTime, default=datetime.datetime.utcnow
    )
    refresh_token = current_app.db.Column(current_app.db.String(255))

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def __repr__(self):
        return f"<User {self.username}>"


class Conversation(current_app.db.Model):
    id = current_app.db.Column(current_app.db.Integer, primary_key=True)
    user_id = current_app.db.Column(
        current_app.db.Integer, current_app.db.ForeignKey("user.id"), nullable=False
    )
    timestamp = current_app.db.Column(
        current_app.db.DateTime, default=current_app.db.func.now()
    )
    input_text = current_app.db.Column(current_app.db.Text)
    response_text = current_app.db.Column(current_app.db.Text)
    input_language = current_app.db.Column(current_app.db.String(20))
    output_language = current_app.db.Column(current_app.db.String(20))
    audio_data = current_app.db.Column(
        current_app.db.LargeBinary
    )  # Optional: Store audio data
    image_data = current_app.db.Column(
        current_app.db.LargeBinary
    )  # Optional: Store generated images
    metadata = current_app.db.Column(JSONB)
    dialogue_state = current_app.db.Column(current_app.db.String(50), default="start")

    user = current_app.db.relationship(
        "User", backref=current_app.db.backref("conversations", lazy=True)
    )

    def __repr__(self):
        return f"<Conversation {self.id} for User {self.user_id}>"
