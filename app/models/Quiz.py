from datetime import datetime

from mongoengine import Document, fields


class Quiz(Document):
    title = fields.DictField()
    difficulty = fields.StringField(max_length=20)
    questions = fields.DictField()
    created_at = fields.DateTimeField(default=datetime.utcnow)

    meta = {"collection": "quizzes", "indexes": ["difficulty", "-created_at"]}

    def to_dict(self):
        return {
            "id": str(self.id),
            "title": self.title,
            "difficulty": self.difficulty,
            "questions": self.questions,
            "created_at": self.created_at.isoformat(),
        }


class QuizResult(Document):
    user_id = fields.StringField(required=True)
    quiz_id = fields.ObjectIdField(required=True)
    score = fields.IntField()
    completed_at = fields.DateTimeField(default=datetime.utcnow)

    meta = {"collection": "quiz_results", "indexes": [("user_id", "quiz_id"), "-completed_at"]}

    def to_dict(self):
        return {
            "id": str(self.id),
            "user_id": self.user_id,
            "quiz_id": str(self.quiz_id),
            "score": self.score,
            "completed_at": self.completed_at.isoformat(),
        }
