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


def save_blood_bank_profile(profile):
    conn = get_connection()
    try:
        cursor = conn.cursor(dictionary=True)
        cursor.execute(
            "SELECT id FROM blood_bank_profile ORDER BY id LIMIT 1 FOR UPDATE"
        )
        existing = cursor.fetchone()
        values = (
            profile["blood_bank_name"],
            profile["phone"],
            profile["city"],
        )
        if existing:
            cursor.execute(
                """
                UPDATE blood_bank_profile
                SET blood_bank_name=%s, phone=%s, city=%s
                WHERE id=%s
                """,
                values + (existing["id"],),
            )
        else:
            cursor.execute(
                """
                INSERT INTO blood_bank_profile
                    (blood_bank_name, email, phone, address, city, state)
                VALUES (%s, '', %s, '', %s, '')
                """,
                values,
            )
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()
