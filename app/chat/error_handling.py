from flask import jsonify


def handle_error(message, status_code):
    response = jsonify({"error": message})
    response.status_code = status_code
    return response


def handle_validation_error(errors):
    response = jsonify({"errors": errors})
    response.status_code = 400
    return response
