from flask import Blueprint, jsonify, request
from datetime import date
from database import fetch_all, fetch_one, get_connection
from utils.decorators import lifelink_api_required
from utils.validators import validate_inventory
from services.inventory_service import create_inventory, update_inventory_units
from services.lifelink_service import public_profile

api_bp = Blueprint("api", __name__, url_prefix="/api/v1")


def log_api(response_status):
    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO api_logs (endpoint, request_method, response_status) VALUES (%s,%s,%s)",
            (request.path, request.method, response_status),
        )
        conn.commit()
    finally:
        conn.close()


@api_bp.get("/inventory")
@lifelink_api_required
def public_inventory():
    conditions = ["expiry_date >= %s"]
    params = [date.today()]
    blood_group = request.args.get("blood_group")
    city = request.args.get("city")
    component = request.args.get("component_type")
    available_only = request.args.get("available_only", "true").lower() != "false"
    if blood_group:
        conditions.append("blood_group=%s")
        params.append(blood_group)
    if city:
        conditions.append("city=%s")
        params.append(city)
    if component:
        conditions.append("component_type=%s")
        params.append(component)
    if available_only:
        conditions.append("available_units > 0")
    conditions.append("status <> 'Unavailable'")
    rows = fetch_all(
        "SELECT id, blood_group, component_type, available_units, city, source, "
        "expiry_date, status FROM inventory WHERE " + " AND ".join(conditions) +
        " ORDER BY expiry_date ASC",
        tuple(params),
    )
    profile = public_profile()
    inventory = [
        {
            "inventory_id": row["id"],
            "blood_group": row["blood_group"],
            "component_type": row["component_type"],
            "available_units": row["available_units"],
            "city": row["city"],
            "source": row["source"],
            "expiry_date": row["expiry_date"].isoformat(),
            "status": row["status"].lower(),
        }
        for row in rows
    ]
    response = jsonify(
        success=True,
        blood_bank={
            "name": profile["blood_bank_name"] if profile else "",
            "city": profile["city"] if profile else "",
        },
        inventory=inventory,
    )
    log_api(200)
    return response


@api_bp.get("/inventory/availability")
@lifelink_api_required
def availability():
    blood_group = request.args.get("blood_group")
    city = request.args.get("city")
    component = request.args.get("component_type")
    if not blood_group:
        log_api(400)
        return jsonify(success=False, error="blood_group is required"), 400
    conditions = [
        "blood_group=%s", "expiry_date >= %s",
        "available_units > 0", "status <> 'Unavailable'",
    ]
    params = [blood_group, date.today()]
    if city:
        conditions.append("city=%s")
        params.append(city)
    if component:
        conditions.append("component_type=%s")
        params.append(component)
    row = fetch_one(
        "SELECT COALESCE(SUM(available_units),0) AS total_available "
        "FROM inventory WHERE " + " AND ".join(conditions),
        tuple(params),
    )
    profile = public_profile()
    response = jsonify(
        success=True,
        blood_group=blood_group,
        city=city or (profile["city"] if profile else ""),
        component_type=component or "Any",
        total_available_units=row["total_available"],
        blood_bank={
            "name": profile["blood_bank_name"] if profile else "",
            "city": profile["city"] if profile else "",
        },
    )
    log_api(200)
    return response


@api_bp.post("/inventory")
@lifelink_api_required
def add_via_api():
    try:
        data = validate_inventory(request.get_json(silent=True) or {})
        inventory_id = create_inventory(data)
        log_api(201)
        return jsonify(success=True, inventory_id=inventory_id), 201
    except ValueError as exc:
        log_api(400)
        return jsonify(success=False, error=str(exc)), 400
    except Exception:
        log_api(500)
        return jsonify(success=False, error="Could not save inventory"), 500


@api_bp.put("/inventory/<int:inventory_id>")
@lifelink_api_required
def update_via_api(inventory_id):
    data = request.get_json(silent=True) or {}
    try:
        available = int(data["available_units"])
        status = update_inventory_units(
            inventory_id, available,
            str(data.get("change_reason", "Updated through LifeLink API")),
        )
        if status is None:
            log_api(404)
            return jsonify(success=False, error="Inventory batch not found"), 404
        log_api(200)
        return jsonify(success=True, status=status)
    except (KeyError, TypeError, ValueError) as exc:
        log_api(400)
        return jsonify(success=False, error=str(exc)), 400


@api_bp.get("/blood-bank/profile")
@lifelink_api_required
def profile():
    profile = public_profile()
    log_api(200)
    if not profile:
        return jsonify(success=False, error="Blood bank profile not configured"), 404
    return jsonify(success=True, blood_bank=profile)
