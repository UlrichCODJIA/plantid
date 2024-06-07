from flask import current_app


def generate_response(inputs):
    try:
        generated_ids = current_app.llava_model.generate(**inputs, max_new_tokens=200)
        response = current_app.llava_processor.batch_decode(
            generated_ids, skip_special_tokens=True
        )[0]
        return response
    except Exception as e:
        raise Exception(f"Error generating response: {e}")
