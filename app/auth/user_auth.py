from dataclasses import dataclass
from datetime import datetime, timezone
from enum import Enum
from functools import wraps
from typing import Dict, Optional

import jwt
import requests
from app.extensions import logger
from app.models.User import User
from flask import current_app
from requests.exceptions import RequestException


class AuthenticationError(Exception):
    """Base exception for authentication errors."""

    pass


class TokenError(AuthenticationError):
    """Raised when there are issues with token generation or validation."""

    pass


class NetworkError(AuthenticationError):
    """Raised when network-related issues occur during authentication."""

    pass


class AuthResponseStatus(Enum):
    """Enumeration of possible authentication response statuses."""

    SUCCESS = "success"
    UNAUTHORIZED = "unauthorized"
    FORBIDDEN = "forbidden"
    ERROR = "error"


@dataclass
class AuthResponse:
    """Data class to represent the authentication response."""

    status: AuthResponseStatus
    user: Optional["User"] = None
    error: Optional[str] = None


@dataclass
class Token:
    """Represents an authentication token with its metadata."""

    value: str
    expiry: datetime

    @property
    def is_expired(self) -> bool:
        """Check if the token has expired."""
        return datetime.now(timezone.utc) >= self.expiry


class TokenManager:
    """Manages authentication tokens for microservice communication."""

    def __init__(self, app_config: dict):
        self.config = app_config
        self._current_token: Optional[Token] = None
        self.jwt_secret = app_config["CHATBOT_JWT_SECRET_KEY"]
        self.refresh_buffer = 300  # 5 minutes

    def _is_token_valid(self) -> bool:
        """
        Checks if the current token is valid and not near expiration.

        Returns:
            bool: True if token is valid and not near expiration, False otherwise.
        """
        if self._current_token is None:
            return False

        try:
            # Decode token to verify signature and expiration
            decoded_token = jwt.decode(self._current_token.value, self.jwt_secret, algorithms=["HS256"])

            # Check if token is nearing expiration
            buffer_time = datetime.now(timezone.utc).timestamp() + self.refresh_buffer
            return decoded_token["exp"] > buffer_time

        except jwt.ExpiredSignatureError:
            return False
        except jwt.InvalidTokenError:
            return False

    def ensure_valid_token(self) -> str:
        """
        Ensures a valid token is available, refreshing if necessary.

        Returns:
            str: A valid token.

        Raises:
            TokenError: If unable to obtain a valid token.
        """
        if not self._is_token_valid():
            self._refresh_token()

        return self._current_token.value

    def _refresh_token(self) -> None:
        """
        Refreshes the authentication token.

        Raises:
            TokenError: If token refresh fails.
        """
        try:
            new_token = self._generate_token()
            decoded_token = jwt.decode(new_token, self.jwt_secret, algorithms=["HS256"])

            expiry = datetime.fromtimestamp(decoded_token["exp"], tz=timezone.utc)
            self._current_token = Token(value=new_token, expiry=expiry)

        except Exception as e:
            raise TokenError(f"Failed to refresh token: {str(e)}") from e

    def _generate_token(self) -> str:
        """
        Generates a new JWT token.

        Returns:
            str: A new JWT token.

        Raises:
            TokenError: If token generation fails.
        """
        try:
            expiry = int(self.config["CHATBOT_JWT_ACCESS_EXPIRES_IN"])
            payload = {
                "exp": datetime.now(timezone.utc).timestamp() + expiry,
                "iat": datetime.now(timezone.utc).timestamp(),
                "service": "chatbot",
            }

            return jwt.encode(payload, self.jwt_secret, algorithm="HS256")
        except Exception as e:
            raise TokenError(f"Failed to generate token: {str(e)}") from e


def retry_on_network_error(retries: int = 3):
    """Decorator to retry a function on network errors."""

    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            for attempt in range(retries):
                try:
                    return func(*args, **kwargs)
                except NetworkError:
                    if attempt == retries - 1:
                        raise
                    logger.warning(f"Network error, retrying... (attempt {attempt + 1}/{retries})")
            return None

        return wrapper

    return decorator


class UserAuthenticator:
    """Handles user authentication against a microservice."""

    def __init__(self):
        self.config = current_app.config
        self.token_manager = TokenManager(current_app.config)

    @retry_on_network_error(retries=3)
    def authenticate_user(self, user_id: str) -> AuthResponse:
        """
        Authenticates a user by their ID.

        Args:
            user_id: The ID of the user to authenticate.

        Returns:
            AuthResponse object containing the authentication status and user data if successful.

        Raises:
            AuthenticationError: If authentication fails due to token or network issues.
        """
        try:
            token = self.token_manager.ensure_valid_token()
            headers = {"Authorization": f"Bearer {token}"}

            response = self._make_auth_request(user_id, headers)
            return self._process_response(response)

        except TokenError as e:
            logger.error(f"Token error during authentication: {e}")
            return AuthResponse(status=AuthResponseStatus.ERROR, error=str(e))
        except Exception as e:
            logger.error(f"Unexpected error during authentication: {e}")
            return AuthResponse(status=AuthResponseStatus.ERROR, error="Internal authentication error")

    def _make_auth_request(self, user_id: str, headers: Dict[str, str]) -> requests.Response:
        """Makes the authentication request to the microservice."""
        try:
            url = f'{self.config["PLANTID_DB_API_BASE_URL"]}/api/auth/user/{user_id}'
            return requests.get(url, headers=headers, timeout=5)
        except RequestException as e:
            logger.error(f"Network error during authentication request: {e}")
            raise NetworkError("Failed to connect to authentication service") from e

    def _process_response(self, response: requests.Response) -> AuthResponse:
        """Processes the authentication response."""
        if response.status_code == 200:
            try:
                user_data = response.json()
                user = User(user_data)
                logger.info(f"User {user.id} authenticated successfully")
                logger.info(f"User data is: {user_data}")
                return AuthResponse(status=AuthResponseStatus.SUCCESS, user=user)
            except (KeyError, ValueError) as e:
                logger.error(f"Invalid user data in response: {e}")
                return AuthResponse(status=AuthResponseStatus.ERROR, error="Invalid user data")
        elif response.status_code == 401:
            return AuthResponse(status=AuthResponseStatus.UNAUTHORIZED)
        elif response.status_code == 403:
            return AuthResponse(status=AuthResponseStatus.FORBIDDEN)
        else:
            return AuthResponse(
                status=AuthResponseStatus.ERROR, error=f"Unexpected status code: {response.status_code}"
            )
