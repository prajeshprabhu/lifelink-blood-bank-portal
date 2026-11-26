from flask import Blueprint, jsonify, render_template, request

from services.lifelink_service import public_profile, save_blood_bank_profile
from utils.decorators import jwt_required_dashboard
from utils.validators import validate_blood_bank_profile

profile_bp = Blueprint("profile", __name__)


@profile_bp.get("/profile")
@jwt_required_dashboard
def profile_page():
    profile = public_profile() or {}
    return render_template("profile.html", profile=profile)


@profile_bp.put("/api/dashboard/profile")
@jwt_required_dashboard
def update_profile():
    try:
        profile = validate_blood_bank_profile(request.get_json(silent=True))
    except ValueError as exc:
        return jsonify(success=False, error=str(exc)), 400

    save_blood_bank_profile(profile)
    return jsonify(success=True, profile=profile)
