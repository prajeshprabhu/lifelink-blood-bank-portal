from flask import Blueprint, render_template, request, jsonify, make_response
from flask_jwt_extended import set_access_cookies, unset_jwt_cookies
from utils.authentication import authenticate

auth_bp = Blueprint("auth", __name__)


@auth_bp.get("/login")
def login_page():
    return render_template("login.html")


@auth_bp.post("/api/auth/login")
def login():
    data = request.get_json(silent=True) or {}
    token = authenticate(str(data.get("username", "")), str(data.get("password", "")))
    if not token:
        return jsonify(success=False, error="Invalid username or password"), 401
    response = make_response(jsonify(success=True))
    set_access_cookies(response, token)
    return response


@auth_bp.post("/api/auth/logout")
def logout():
    response = make_response(jsonify(success=True))
    unset_jwt_cookies(response)
    response.delete_cookie("access_token_cookie", path="/api/auth")
    return response
