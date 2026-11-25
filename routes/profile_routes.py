from flask import Blueprint, render_template, request, jsonify
from database import get_connection
from utils.decorators import jwt_required_dashboard

profile_bp = Blueprint("profile", __name__)


@profile_bp.get("/profile")
@jwt_required_dashboard
def profile_page():
    return render_template("profile.html")


@profile_bp.get("/api/profile")
@jwt_required_dashboard
def get_profile():
    conn = get_connection()
    try:
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM blood_bank_profile ORDER BY id LIMIT 1")
        row = cursor.fetchone()
        return jsonify(success=True, profile=row)
    finally:
        conn.close()


@profile_bp.put("/api/profile")
@jwt_required_dashboard
def update_profile():
    data = request.get_json(silent=True) or {}
    required = ["blood_bank_name", "email", "phone", "address", "city", "state"]
    if any(not str(data.get(field, "")).strip() for field in required):
        return jsonify(success=False, error="All profile fields are required"), 400
    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM blood_bank_profile ORDER BY id LIMIT 1")
        row = cursor.fetchone()
        values = tuple(data[field].strip() for field in required)
        if row:
            cursor.execute(
                "UPDATE blood_bank_profile SET blood_bank_name=%s,email=%s,phone=%s,address=%s,city=%s,state=%s,updated_at=CURRENT_TIMESTAMP WHERE id=%s",
                values + (row[0],),
            )
        else:
            cursor.execute(
                "INSERT INTO blood_bank_profile (blood_bank_name,email,phone,address,city,state) VALUES (%s,%s,%s,%s,%s,%s)",
                values,
            )
        conn.commit()
        return jsonify(success=True)
    finally:
        conn.close()
