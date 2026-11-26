import unittest
from datetime import date

from utils.validators import validate_inventory


class InventoryDefaultsTests(unittest.TestCase):
    def test_removed_form_fields_receive_whole_blood_defaults(self):
        donation_date = date(2026, 11, 26)
        payload = {
            "blood_group": "O+",
            "units_collected": 2,
            "donor_name": "Example Donor",
            "donor_phone": "+919876543210",
            "city": "Pune",
            "source": "Direct Blood Donation",
            "donation_date": donation_date.isoformat(),
        }

        inventory = validate_inventory(payload)

        self.assertEqual(inventory["component_type"], "Whole Blood")
        self.assertEqual(inventory["collection_date"], donation_date)
        self.assertEqual(inventory["expiry_date"], date(2027, 1, 7))

    def test_explicit_inventory_dates_and_component_remain_supported(self):
        payload = {
            "blood_group": "O+",
            "component_type": "Platelets",
            "units_collected": 2,
            "donor_name": "Example Donor",
            "donor_phone": "+919876543210",
            "city": "Pune",
            "source": "Direct Blood Donation",
            "donation_date": "2026-11-26",
            "collection_date": "2026-11-27",
            "expiry_date": "2026-12-10",
        }

        inventory = validate_inventory(payload)

        self.assertEqual(inventory["component_type"], "Platelets")
        self.assertEqual(inventory["collection_date"], date(2026, 11, 27))
        self.assertEqual(inventory["expiry_date"], date(2026, 12, 10))


if __name__ == "__main__":
    unittest.main()
