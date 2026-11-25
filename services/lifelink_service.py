from datetime import date
from database import get_connection


def public_profile():
    conn = get_connection()
    try:
        cursor = conn.cursor(dictionary=True)
        cursor.execute(
            "SELECT blood_bank_name, email, phone, address, city, state "
            "FROM blood_bank_profile ORDER BY id LIMIT 1"
        )
        return cursor.fetchone()
    finally:
        conn.close()
