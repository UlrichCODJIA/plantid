from multilingual_webapp.app.models.models import Conversation
from multilingual_webapp.app.extensions import db


def save_conversation(
    user_id,
    input_text,
    response_text,
    input_language,
    output_language,
    dialogue_state,
    image_path,
):
    new_conversation = Conversation(
        user_id=user_id,
        input_text=input_text,
        response_text=response_text,
        input_language=input_language,
        output_language=output_language,
        dialogue_state=dialogue_state,
        image_path=image_path,
    )
    db.session.add(new_conversation)
    db.session.commit()
