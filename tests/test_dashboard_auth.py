import unittest
from datetime import timedelta

from flask import Flask
from flask_jwt_extended import JWTManager, create_access_token

from routes.auth_routes import auth_bp
from routes.dashboard_routes import dashboard_bp


class DashboardAuthenticationTests(unittest.TestCase):
    def setUp(self):
        app = Flask(__name__)
        app.config.update(
            JWT_SECRET_KEY="test-secret",
            JWT_TOKEN_LOCATION=["cookies"],
            JWT_COOKIE_CSRF_PROTECT=False,
        )
        JWTManager().init_app(app)
        app.register_blueprint(auth_bp)
        app.register_blueprint(dashboard_bp)
        self.client = app.test_client()

    def test_invalid_cookie_redirects_to_login(self):
        self.client.set_cookie("access_token_cookie", "not-a-valid-jwt")

        response = self.client.get("/")

        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.headers["Location"], "/login")

    def test_expired_cookie_redirects_to_login(self):
        with self.client.application.app_context():
            token = create_access_token("admin", expires_delta=timedelta(seconds=-1))
        self.client.set_cookie("access_token_cookie", token)

        response = self.client.get("/")

        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.headers["Location"], "/login")


if __name__ == "__main__":
    unittest.main()
