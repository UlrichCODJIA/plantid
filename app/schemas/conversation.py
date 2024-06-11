from marshmallow import Schema, fields, validate


class CreateConversationSchema(Schema):
    user_id = fields.Str(required=True)
    title = fields.Str(required=True)
    input_language = fields.Str(validate=validate.Length(min=2, max=10))
    output_language = fields.Str(validate=validate.Length(min=2, max=10))
    dialogue_state = fields.Str(
        validate=validate.OneOf(
            ["greeting", "conversing", "confirming", "generating_image", "end"]
        )
    )


class UpdateConversationSchema(Schema):
    title = fields.Str()
    dialogue_state = fields.Str(
        validate=validate.OneOf(
            ["greeting", "conversing", "confirming", "generating_image", "end"]
        )
    )
