from flask import current_app
import requests

from app.chatbot.utils.auth import MicroserviceToken
from app.models.User import User
from app.utils.utils import (
    generate_microservice_token,
    temporary_jwt_secret_key,
)

microservice_token = MicroserviceToken()


def authenticate_user(user_id):
    try:
        if not microservice_token.is_valid():
            with temporary_jwt_secret_key(
                current_app, current_app.config["CHATBOT_JWT_SECRET_KEY"]
            ):
                token = generate_microservice_token()
                microservice_token.refresh(
                    token,
                    current_app.config["CHATBOT_JWT_ACCESS_EXPIRES_IN"],
                )

        headers = {"Authorization": f"Bearer {microservice_token.token}"}
        response = requests.get(
            f'{current_app.config["PLANTID_DB_API_BASE_URL"]}/api/auth/user/{user_id}',
            headers=headers,
        )

        if response.status_code == 200:
            user_data = response.json()
            user = User(user_data)
            return user
        elif response.status_code == 401:
            return None
        elif response.status_code == 403:
            return None
        else:
            return None
    except requests.exceptions.RequestException:
        return None
