from flask import Blueprint, render_template, redirect, url_for
from flask_jwt_extended import get_jwt_identity, verify_jwt_in_request
from database import fetch_all, fetch_one
from services.inventory_service import refresh_expired_statuses
from utils.decorators import jwt_required_dashboard
from database import get_connection

dashboard_bp = Blueprint("dashboard", __name__)


def dashboard_data():
    conn = get_connection()
    try:
        cursor = conn.cursor(dictionary=True)
        refresh_expired_statuses(cursor)
        cursor.execute(
            """
            SELECT
              COALESCE(SUM(units_collected),0) AS total_units,
              COALESCE(SUM(available_units),0) AS available_units,
              COALESCE(SUM(reserved_units),0) AS reserved_units,
              COALESCE(SUM(CASE WHEN status='Expired' THEN units_collected ELSE 0 END),0) AS expired_batches
            FROM inventory
            """
        )
        summary = cursor.fetchone()
        cursor.execute("SELECT COUNT(*) AS total FROM inventory_history WHERE change_reason='Donation batch added'")
        donations = cursor.fetchone()["total"]
        cursor.execute(
            """
            SELECT blood_group,
                   COALESCE(SUM(available_units),0) AS available_units
            FROM inventory
            WHERE status <> 'Expired'
            GROUP BY blood_group
            """
        )
        stock = cursor.fetchall()
        cursor.execute(
            "SELECT * FROM inventory ORDER BY created_at DESC LIMIT 5"
        )
        recent_donations = cursor.fetchall()
        cursor.execute(
            """
            SELECT h.*, i.blood_group
            FROM inventory_history h
            JOIN inventory i ON i.id=h.inventory_id
            ORDER BY h.changed_at DESC LIMIT 8
            """
        )
        history = cursor.fetchall()
        cursor.execute(
            """
            SELECT * FROM inventory
            WHERE status <> 'Expired'
              AND available_units < 5
            ORDER BY available_units ASC LIMIT 10
            """
        )
        low_stock = cursor.fetchall()
        cursor.execute(
            """
            SELECT * FROM inventory
            WHERE status <> 'Expired'
              AND expiry_date BETWEEN CURDATE() AND DATE_ADD(CURDATE(), INTERVAL 30 DAY)
            ORDER BY expiry_date ASC LIMIT 10
            """
        )
        near_expiry = cursor.fetchall()
        cursor.execute(
            "SELECT * FROM inventory WHERE status='Expired' ORDER BY expiry_date DESC LIMIT 10"
        )
        expired = cursor.fetchall()
        conn.commit()
        summary["total_donations"] = donations
        return {
            "summary": summary,
            "stock": stock,
            "recent_donations": recent_donations,
            "history": history,
            "low_stock": low_stock,
            "near_expiry": near_expiry,
            "expired": expired,
        }
    finally:
        conn.close()


@dashboard_bp.get("/")
def dashboard():
    verify_jwt_in_request(optional=True)
    if not get_jwt_identity():
        return redirect(url_for("auth.login_page"))
    return render_template("dashboard.html")


@dashboard_bp.get("/api/dashboard")
@jwt_required_dashboard
def dashboard_api():
    from flask import jsonify
    return jsonify(dashboard_data())
