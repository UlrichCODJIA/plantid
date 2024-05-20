from flask import Blueprint, request, jsonify, current_app
from flask_jwt_extended import (
    create_access_token,
    create_refresh_token,
    get_jwt,
    get_jwt_identity,
    jwt_required,
)
from models import db, User

auth_blueprint = Blueprint("auth", __name__)


@current_app.jwt.token_in_blocklist_loader
def check_if_token_is_revoked(jwt_header, jwt_payload):
    jti = jwt_payload["jti"]
    token_in_redis = current_app.redis_client.get(jti)
    return token_in_redis is not None


@auth_blueprint.route("/register", methods=["POST"])
def register():
    try:
        data = request.get_json()
        username = data.get("username")
        password = data.get("password")
        email = data.get("email")
        language_preference = data.get("language_preference", "English")

        if not all([username, password, email]):
            return jsonify({"error": "Missing required fields"}), 400

        if User.query.filter_by(username=username).first():
            return jsonify({"error": "Username already exists"}), 400

        if User.query.filter_by(email=email).first():
            return jsonify({"error": "Email already exists"}), 400

        user = User(
            username=username,
            email=email,
            language_preference=language_preference,
        )
        user.set_password(password)
        db.session.add(user)
        db.session.commit()

        return jsonify({"message": "User registered successfully"}), 201

    except Exception as e:
        db.session.rollback()  # Rollback transaction on error
        return jsonify({"error": str(e)}), 500


@auth_blueprint.route("/login", methods=["POST"])
def login():
    try:
        data = request.get_json()
        username = data.get("username")
        password = data.get("password")

        if not all([username, password]):
            return jsonify({"error": "Missing username or password"}), 400

        user = User.query.filter_by(username=username).first()
        if user and user.check_password(password):
            refresh_token = create_refresh_token(identity=user.id)
            access_token = create_access_token(identity=user.id)

            # Optionally store the refresh token in the database
            user.refresh_token = refresh_token
            db.session.commit()

            return (
                jsonify(
                    {
                        "message": "Logged in successfully",
                        "access_token": access_token,
                        "refresh_token": refresh_token,
                    }
                ),
                200,
            )
        else:
            return jsonify({"error": "Invalid credentials"}), 401

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@auth_blueprint.route("/refresh", methods=["POST"])
@jwt_required(refresh=True)
def refresh():
    try:
        identity = get_jwt_identity()
        user = User.query.get(identity)

        # Check if refresh token is in blocklist
        current_refresh_token = get_jwt()["jti"]
        if check_if_token_is_revoked(
            jwt_header=None, jwt_payload={"jti": current_refresh_token}
        ):
            return (
                jsonify(
                    {"error": "Refresh token has been revoked. Please log in again."}
                ),
                401,
            )

        # Check if the refresh token exists in the database
        if (
            not user
            or not user.refresh_token
            or user.refresh_token != current_refresh_token
        ):
            return (
                jsonify({"error": "Invalid refresh token. Please log in again."}),
                401,
            )

        # Invalidate the old refresh token (add to blocklist)
        current_app.redis_client.set(
            user.refresh_token,
            "",
            ex=current_app.app.config["JWT_REFRESH_TOKEN_EXPIRES"],
        )
        user.refresh_token = None
        db.session.commit()

        # Create new tokens
        refresh_token = create_refresh_token(identity=identity)
        access_token = create_access_token(identity=identity)
        user.refresh_token = refresh_token
        db.session.commit()

        return (
            jsonify({"access_token": access_token, "refresh_token": refresh_token}),
            200,
        )

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@auth_blueprint.route("/profile", methods=["GET", "POST"])
@jwt_required()
def profile():
    try:
        user_id = get_jwt_identity()
        user = User.query.get(user_id)
        if not user:
            return jsonify({"error": "User not found"}), 404

        if request.method == "POST":
            data = request.get_json()
            # Update allowed fields
            allowed_fields = [
                "email",
                "first_name",
                "last_name",
                "language_preference",
                "voice_preference",
                "image_generation_style",
            ]
            for field in allowed_fields:
                if field in data:
                    setattr(user, field, data[field])

            db.session.commit()
            return jsonify({"message": "Profile updated successfully"}), 200

        # GET request - Return user profile
        return (
            jsonify(
                {
                    "username": user.username,
                    "email": user.email,
                    "first_name": user.first_name,
                    "last_name": user.last_name,
                    "language_preference": user.language_preference,
                    "voice_preference": user.voice_preference,
                    "image_generation_style": user.image_generation_style,
                    # ... add other fields as needed ...
                }
            ),
            200,
        )

    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500


@auth_blueprint.route("/logout", methods=["POST"])
@jwt_required()
def logout():
    try:
        jti = get_jwt()["jti"]  # Get the JWT ID
        current_app.redis_client.set(
            jti, "", ex=current_app.app.config["JWT_ACCESS_TOKEN_EXPIRES"]
        )  # Add to blocklist

        return jsonify({"message": "Logged out successfully"})
    except Exception as e:
        return jsonify({"error": str(e)}), 500
