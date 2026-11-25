from flask import request
from flask_jwt_extended import create_access_token
from werkzeug.security import check_password_hash, generate_password_hash
from config import Config
from database import fetch_one, execute


def initialize_admin():
    row = fetch_one("SELECT id, password_hash FROM admin_users WHERE username=%s", (Config.ADMIN_USERNAME,))
    if row:
        if Config.ADMIN_PASSWORD_HASH and row["password_hash"] != Config.ADMIN_PASSWORD_HASH:
            execute(
                "UPDATE admin_users SET password_hash=%s, updated_at=CURRENT_TIMESTAMP WHERE id=%s",
                (Config.ADMIN_PASSWORD_HASH, row["id"]),
            )
        return
    password_hash = Config.ADMIN_PASSWORD_HASH or generate_password_hash(Config.ADMIN_PASSWORD)
    execute(
        "INSERT INTO admin_users (username, password_hash) VALUES (%s, %s)",
        (Config.ADMIN_USERNAME, password_hash),
    )


def authenticate(username, password):
    row = fetch_one(
        "SELECT id, username, password_hash FROM admin_users WHERE username=%s",
        (username,),
    )
    if not row or not check_password_hash(row["password_hash"], password):
        return None
    return create_access_token(identity=str(row["id"]), additional_claims={"username": row["username"]})
