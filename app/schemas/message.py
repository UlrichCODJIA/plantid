from marshmallow import Schema, fields, validate


class CreateMessageSchema(Schema):
    conversation_id = fields.Str(required=True)
    text = fields.Str()
    sender = fields.Str(required=True, validate=validate.OneOf(["user", "bot"]))
    image_url = fields.Url()
    audio_data = fields.Str()
