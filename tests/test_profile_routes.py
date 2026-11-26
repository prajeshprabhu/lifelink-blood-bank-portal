import os
import unittest
from unittest.mock import patch

from flask import Flask
from flask_jwt_extended import JWTManager, create_access_token

from routes.profile_routes import profile_bp


PROFILE = {
    "blood_bank_name": "Example Blood Bank",
    "phone": "+91 9876543210",
    "city": "Mangaluru",
}


class BloodBankProfileRouteTests(unittest.TestCase):
    def setUp(self):
        project_root = os.path.dirname(os.path.dirname(__file__))
        app = Flask(
            __name__,
            template_folder=os.path.join(project_root, "templates"),
            static_folder=os.path.join(project_root, "static"),
        )
        app.config.update(
            JWT_SECRET_KEY="test-secret-that-is-at-least-thirty-two-bytes",
            JWT_TOKEN_LOCATION=["cookies"],
            JWT_COOKIE_CSRF_PROTECT=False,
        )
        JWTManager().init_app(app)
        app.register_blueprint(profile_bp)
        self.client = app.test_client()

    def authenticate(self):
        with self.client.application.app_context():
            token = create_access_token("admin")
        self.client.set_cookie("access_token_cookie", token)

    @patch("routes.profile_routes.public_profile", return_value=PROFILE)
    def test_profile_page_requires_authentication_and_loads_profile(self, public_profile):
        response = self.client.get("/profile")
        self.assertEqual(response.status_code, 401)

        self.authenticate()
        response = self.client.get("/profile")

        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Example Blood Bank", response.data)
        self.assertIn(b"+91 9876543210", response.data)
        self.assertIn(b'<option value="Mangalore"', response.data)
        self.assertNotIn(b'<option value="Mangaluru"', response.data)
        self.assertNotIn(b'name="email"', response.data)
        self.assertNotIn(b'name="address"', response.data)
        self.assertNotIn(b'name="state"', response.data)

    @patch("routes.profile_routes.save_blood_bank_profile")
    def test_authenticated_admin_can_save_profile(self, save_profile):
        self.authenticate()

        response = self.client.put("/api/dashboard/profile", json=PROFILE)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.get_json()["profile"], PROFILE)
        save_profile.assert_called_once_with(PROFILE)

    @patch("routes.profile_routes.save_blood_bank_profile")
    def test_rejects_invalid_profile_without_saving(self, save_profile):
        self.authenticate()
        invalid_profile = dict(PROFILE, phone="not a phone")

        response = self.client.put("/api/dashboard/profile", json=invalid_profile)

        self.assertEqual(response.status_code, 400)
        save_profile.assert_not_called()


if __name__ == "__main__":
    unittest.main()
