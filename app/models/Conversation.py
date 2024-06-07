from sqlalchemy.dialects.postgresql import JSONB

from multilingual_webapp.app.extensions import db


class Conversation(db.Model):
    """
    Represents a conversation in the database.

    Attributes:
        id (int): The primary key of the conversation.
        user_id (str): The ID of the user associated with the conversation.
        timestamp (datetime): The timestamp of the conversation.
        input_text (str): The input text of the conversation.
        response_text (str): The response text of the conversation.
        input_language (str): The input language of the conversation.
        output_language (str): The output language of the conversation.
        audio_data (bytes): The audio data associated with the conversation.
        image_data (bytes): The image data associated with the conversation.
        metadatas (dict): Additional metadata associated with the conversation.
        dialogue_state (str): The current dialogue state of the conversation.
    """

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.String(50), nullable=False)
    timestamp = db.Column(db.DateTime, default=db.func.now())
    input_text = db.Column(db.Text)
    response_text = db.Column(db.Text)
    input_language = db.Column(db.String(20))
    output_language = db.Column(db.String(20))
    audio_data = db.Column(db.LargeBinary)
    image_data = db.Column(db.LargeBinary)
    metadatas = db.Column(JSONB)
    dialogue_state = db.Column(db.String(50), default="start")

    def __repr__(self):
        return f"<Conversation {self.id} for User {self.user_id}>"
