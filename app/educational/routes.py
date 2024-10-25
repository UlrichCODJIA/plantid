from app.auth.user_auth import AuthResponseStatus, UserAuthenticator
from app.models.Quiz import Quiz, QuizResult
from flask import Blueprint, jsonify, request
from flask_jwt_extended import get_jwt_identity, jwt_required

from plantid.app.chat.error_handling import handle_error

educational_blueprint = Blueprint("educational", __name__, url_prefix="/api/v1")


@educational_blueprint.route("/quizzes", methods=["GET"])
@jwt_required()
def get_quizzes():
    user_id = get_jwt_identity()
    authenticator = UserAuthenticator()
    response = authenticator.authenticate_user(user_id)
    if not response.status == AuthResponseStatus.SUCCESS:
        return handle_error("Unauthorized access", 403)
    user = response.user

    difficulty = request.args.get("difficulty", user.expertise_level)

    quizzes = Quiz.objects(difficulty=difficulty)

    return jsonify({"quizzes": [format_quiz(quiz, user.preferred_language) for quiz in quizzes]})


@educational_blueprint.route("/quiz/<int:quiz_id>/submit", methods=["POST"])
@jwt_required()
def submit_quiz(quiz_id):
    user_id = get_jwt_identity()
    data = request.json

    if not data or "answers" not in data:
        return jsonify({"error": "No answers provided"}), 400

    quiz = Quiz.objects.get_or_404(_id=quiz_id)
    score = calculate_quiz_score(quiz, data["answers"])

    result = QuizResult(user_id=user_id, quiz_id=quiz_id, score=score)
    result.save()

    return jsonify({"score": score, "total": len(quiz.questions)})


def format_quiz(quiz, language):
    return {
        "id": quiz.id,
        "title": quiz.title.get(language, quiz.title["en"]),
        "difficulty": quiz.difficulty,
        "question_count": len(quiz.questions),
    }


def calculate_quiz_score(quiz, user_answers):
    correct_answers = 0
    for q_idx, question in enumerate(quiz.questions):
        if q_idx < len(user_answers) and user_answers[q_idx] == question["correct_answer"]:
            correct_answers += 1
    return correct_answers
