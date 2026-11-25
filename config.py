import os
from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(__file__), ".env"))


class Config:
    SECRET_KEY = os.getenv("SECRET_KEY", "development-secret")
    JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "development-jwt-secret")
    JWT_TOKEN_LOCATION = ["cookies"]
    JWT_COOKIE_CSRF_PROTECT = False
    JWT_COOKIE_SECURE = os.getenv("JWT_COOKIE_SECURE", "false").lower() == "true"
    JWT_COOKIE_SAMESITE = "Lax"
    JWT_ACCESS_COOKIE_PATH = "/"
    JWT_ACCESS_TOKEN_EXPIRES = 3600

    MYSQL = {
        "host": os.getenv("MYSQL_HOST", "localhost"),
        "port": int(os.getenv("MYSQL_PORT", "3306")),
        "user": os.getenv("MYSQL_USER", "root"),
        "password": os.getenv("MYSQL_PASSWORD", ""),
        "database": os.getenv("MYSQL_DATABASE", "blood_bank_portal"),
        "autocommit": False,
    }
    mysql_ssl_ca = os.getenv("MYSQL_SSL_CA", "").strip()
    if mysql_ssl_ca:
        MYSQL.update(
            {
                "ssl_ca": mysql_ssl_ca,
                "ssl_verify_cert": os.getenv(
                    "MYSQL_SSL_VERIFY_CERT", "true"
                ).lower() == "true",
                "ssl_verify_identity": os.getenv(
                    "MYSQL_SSL_VERIFY_IDENTITY", "true"
                ).lower() == "true",
            }
        )

    ADMIN_USERNAME = os.getenv("ADMIN_USERNAME", "bloodbank")
    ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "change-this-password")
    ADMIN_PASSWORD_HASH = os.getenv("ADMIN_PASSWORD_HASH", "")
    LIFELINK_API_SECRET = os.getenv("LIFELINK_API_SECRET", "")
    CORS_ALLOWED_ORIGINS = [
        origin.strip()
        for origin in os.getenv("CORS_ALLOWED_ORIGINS", "").split(",")
        if origin.strip()
    ]

