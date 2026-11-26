from flask import Blueprint, render_template, redirect, url_for
from flask_jwt_extended import get_jwt_identity, verify_jwt_in_request
from flask_jwt_extended.exceptions import JWTExtendedException
from jwt.exceptions import InvalidTokenError
from services.inventory_service import refresh_expired_statuses
from utils.decorators import jwt_required_dashboard
from database import get_connection

dashboard_bp = Blueprint("dashboard", __name__)


def dashboard_data():
    conn = get_connection()
    try:
        cursor = conn.cursor(dictionary=True)
        refresh_expired_statuses(cursor)
        conn.commit()
        cursor.execute(
            """
            SELECT blood_group,
                   COALESCE(SUM(units_collected),0) AS total_units,
                   COALESCE(SUM(CASE WHEN status <> 'Expired'
                                     THEN available_units ELSE 0 END),0) AS available_units,
                   COALESCE(SUM(reserved_units),0) AS reserved_units,
                   COALESCE(SUM(CASE WHEN status='Expired'
                                     THEN units_collected ELSE 0 END),0) AS expired_batches,
                   COALESCE(SUM(CASE WHEN status <> 'Expired' THEN 1 ELSE 0 END),0) AS active_batches,
                   (SELECT COUNT(*) FROM inventory_history
                    WHERE change_reason='Donation batch added') AS total_donations
            FROM inventory
            GROUP BY blood_group WITH ROLLUP
            """
        )
        summary = None
        stock = []
        for row in cursor.fetchall():
            if row["blood_group"] is None:
                summary = {
                    "total_units": row["total_units"],
                    "available_units": row["available_units"],
                    "reserved_units": row["reserved_units"],
                    "expired_batches": row["expired_batches"],
                    "total_donations": row["total_donations"],
                }
            elif row["active_batches"]:
                stock.append(
                    {
                        "blood_group": row["blood_group"],
                        "available_units": row["available_units"],
                    }
                )
        if summary is None:
            summary = {
                "total_units": 0,
                "available_units": 0,
                "reserved_units": 0,
                "expired_batches": 0,
                "total_donations": 0,
            }

        inventory_sections = (
            (
                "recent_donations",
                "SELECT * FROM inventory ORDER BY created_at DESC LIMIT 5",
            ),
            (
                "low_stock",
                "SELECT * FROM inventory WHERE status <> 'Expired' "
                "AND available_units < 5 ORDER BY available_units ASC LIMIT 10",
            ),
            (
                "near_expiry",
                "SELECT * FROM inventory WHERE status <> 'Expired' "
                "AND expiry_date BETWEEN CURDATE() "
                "AND DATE_ADD(CURDATE(), INTERVAL 30 DAY) "
                "ORDER BY expiry_date ASC LIMIT 10",
            ),
            (
                "expired",
                "SELECT * FROM inventory WHERE status='Expired' "
                "ORDER BY expiry_date DESC LIMIT 10",
            ),
        )
        inventory_sql = " UNION ALL ".join(
            "SELECT %s AS section, selected_inventory.* "
            f"FROM ({query}) AS selected_inventory"
            for _, query in inventory_sections
        )
        cursor.execute(inventory_sql, tuple(name for name, _ in inventory_sections))
        inventories = {name: [] for name, _ in inventory_sections}
        for row in cursor.fetchall():
            section = row.pop("section")
            inventories[section].append(row)

        cursor.execute(
            """
            SELECT h.*, i.blood_group
            FROM inventory_history h
            JOIN inventory i ON i.id=h.inventory_id
            ORDER BY h.changed_at DESC LIMIT 8
            """
        )
        history = cursor.fetchall()
        inventories["recent_donations"].sort(
            key=lambda row: row["created_at"], reverse=True
        )
        inventories["low_stock"].sort(key=lambda row: row["available_units"])
        inventories["near_expiry"].sort(key=lambda row: row["expiry_date"])
        inventories["expired"].sort(
            key=lambda row: row["expiry_date"], reverse=True
        )
        return {
            "summary": summary,
            "stock": stock,
            "recent_donations": inventories["recent_donations"],
            "history": history,
            "low_stock": inventories["low_stock"],
            "near_expiry": inventories["near_expiry"],
            "expired": inventories["expired"],
        }
    finally:
        conn.close()


@dashboard_bp.get("/")
def dashboard():
    try:
        verify_jwt_in_request(optional=True)
    except (JWTExtendedException, InvalidTokenError):
        return redirect(url_for("auth.login_page"))
    if not get_jwt_identity():
        return redirect(url_for("auth.login_page"))
    return render_template("dashboard.html")


@dashboard_bp.get("/api/dashboard")
@jwt_required_dashboard
def dashboard_api():
    from flask import jsonify
    return jsonify(dashboard_data())
