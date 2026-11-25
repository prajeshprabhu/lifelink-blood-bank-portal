from functools import wraps
from flask import jsonify, request
from flask_jwt_extended import verify_jwt_in_request
from config import Config


def jwt_required_dashboard(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        verify_jwt_in_request()
        return fn(*args, **kwargs)
    return wrapper


def lifelink_api_required(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        auth = request.headers.get("Authorization", "")
        supplied = auth[7:].strip() if auth.lower().startswith("bearer ") else ""
        if not Config.LIFELINK_API_SECRET or supplied != Config.LIFELINK_API_SECRET:
            return jsonify(success=False, error="Unauthorized"), 401
        return fn(*args, **kwargs)
    return wrapper
