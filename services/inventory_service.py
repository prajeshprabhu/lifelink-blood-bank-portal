from datetime import date
from database import get_connection


def derive_status(row):
    if row["expiry_date"] <= date.today():
        return "Expired"
    if row["available_units"] == 0:
        return "Reserved" if row["reserved_units"] > 0 else "Unavailable"
    if row["reserved_units"] > 0:
        return "Partially Reserved"
    return "Available"


def refresh_expired_statuses(cursor):
    cursor.execute(
        """
        UPDATE inventory
        SET status='Expired', updated_at=CURRENT_TIMESTAMP
        WHERE expiry_date < %s
          AND status <> 'Expired'
        """,
        (date.today(),),
    )


def create_inventory(data):
    conn = get_connection()
    try:
        cursor = conn.cursor(dictionary=True)
        cursor.execute(
            """
            INSERT INTO inventory
            (blood_group, component_type, units_collected, available_units,
             reserved_units, donor_name, donor_phone, city, source,
             donation_date, collection_date, expiry_date, status, remarks)
            VALUES (%s,%s,%s,%s,0,%s,%s,%s,%s,%s,%s,%s,'Available',%s)
            """,
            (
                data["blood_group"], data["component_type"], data["units_collected"],
                data["units_collected"], data["donor_name"], data["donor_phone"],
                data["city"], data["source"], data["donation_date"],
                data["collection_date"], data["expiry_date"], data["remarks"],
            ),
        )
        inventory_id = cursor.lastrowid
        cursor.execute(
            """
            INSERT INTO inventory_history
            (inventory_id, previous_units, updated_units, previous_status,
             updated_status, change_reason)
            VALUES (%s,0,%s,'Unavailable','Available','Donation batch added')
            """,
            (inventory_id, data["units_collected"]),
        )
        conn.commit()
        return inventory_id
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def update_inventory_units(inventory_id, available_units, reason):
    conn = get_connection()
    try:
        cursor = conn.cursor(dictionary=True)
        cursor.execute(
            "SELECT * FROM inventory WHERE id=%s FOR UPDATE",
            (inventory_id,),
        )
        row = cursor.fetchone()
        if not row:
            return None
        if available_units < 0 or available_units > row["units_collected"]:
            raise ValueError("Available units must be between 0 and units collected")

        previous_status = row["status"]
        reserved_units = max(row["reserved_units"], row["units_collected"] - available_units)
        reserved_units = min(reserved_units, row["units_collected"])
        status_row = {
            "expiry_date": row["expiry_date"],
            "available_units": available_units,
            "reserved_units": reserved_units,
        }
        if reason == "Marked unavailable":
            status = "Unavailable"
        else:
            status = derive_status(status_row)

        cursor.execute(
            """
            UPDATE inventory
            SET available_units=%s, reserved_units=%s, status=%s,
                updated_at=CURRENT_TIMESTAMP
            WHERE id=%s
            """,
            (available_units, reserved_units, status, inventory_id),
        )
        cursor.execute(
            """
            INSERT INTO inventory_history
            (inventory_id, previous_units, updated_units, previous_status,
             updated_status, change_reason)
            VALUES (%s,%s,%s,%s,%s,%s)
            """,
            (
                inventory_id, row["available_units"], available_units,
                previous_status, status, reason,
            ),
        )
        conn.commit()
        return status
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()
