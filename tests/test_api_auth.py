import unittest
from unittest.mock import patch

from flask import Flask

from routes.api_routes import api_bp


class APIAuthenticationTests(unittest.TestCase):
    def setUp(self):
        app = Flask(__name__)
        app.register_blueprint(api_bp)
        self.client = app.test_client()

    @patch("routes.api_routes.log_api")
    @patch("routes.api_routes.public_profile", return_value=None)
    @patch(
        "routes.api_routes.fetch_one",
        return_value={"total_available": 4},
    )
    def test_availability_is_public(self, fetch_one, public_profile, log_api):
        response = self.client.get(
            "/api/v1/inventory/availability?blood_group=O%2B"
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.get_json()["total_available_units"], 4)

    @patch("routes.api_routes.log_api")
    @patch("routes.api_routes.public_profile", return_value=None)
    @patch("routes.api_routes.fetch_all", return_value=[])
    def test_inventory_listing_is_public(self, fetch_all, public_profile, log_api):
        response = self.client.get("/api/v1/inventory")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.get_json()["inventory"], [])

    @patch("routes.api_routes.log_api")
    @patch(
        "routes.api_routes.public_profile",
        return_value={"blood_bank_name": "Example Blood Bank"},
    )
    def test_profile_is_public(self, public_profile, log_api):
        response = self.client.get("/api/v1/blood-bank/profile")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.get_json()["blood_bank"]["blood_bank_name"],
            "Example Blood Bank",
        )

    def test_inventory_writes_still_require_the_bearer_key(self):
        with patch("utils.decorators.Config.LIFELINK_API_SECRET", "test-secret"):
            create_response = self.client.post("/api/v1/inventory", json={})
            update_response = self.client.put(
                "/api/v1/inventory/1",
                json={"available_units": 1},
            )

        self.assertEqual(create_response.status_code, 401)
        self.assertEqual(update_response.status_code, 401)


if __name__ == "__main__":
    unittest.main()
