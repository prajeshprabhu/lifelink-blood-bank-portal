from flask import Blueprint, render_template, request, jsonify
from database import fetch_all, fetch_one, get_connection
from utils.decorators import jwt_required_dashboard
from utils.validators import validate_inventory
from services.inventory_service import create_inventory, update_inventory_units

inventory_bp = Blueprint("inventory", __name__)


@inventory_bp.get("/inventory/add")
@jwt_required_dashboard
def add_page():
    return render_template("add_inventory.html")


@inventory_bp.get("/inventory/manage")
@jwt_required_dashboard
def manage_page():
    return render_template("manage_inventory.html")


@inventory_bp.get("/inventory/history")
@jwt_required_dashboard
def history_page():
    return render_template("inventory_history.html")


@inventory_bp.post("/api/inventory")
@jwt_required_dashboard
def add_inventory_api():
    try:
        data = validate_inventory(request.get_json(silent=True) or {})
        inventory_id = create_inventory(data)
        return jsonify(success=True, inventory_id=inventory_id), 201
    except ValueError as exc:
        return jsonify(success=False, error=str(exc)), 400
    except Exception as exc:
        return jsonify(success=False, error="Could not save inventory"), 500


@inventory_bp.get("/api/inventory")
@jwt_required_dashboard
def list_inventory():
    page = max(int(request.args.get("page", 1)), 1)
    per_page = min(max(int(request.args.get("per_page", 10)), 1), 100)
    offset = (page - 1) * per_page
    conditions = []
    params = []
    filters = {
        "blood_group": "blood_group=%s",
        "city": "city LIKE %s",
        "source": "source=%s",
        "component_type": "component_type=%s",
        "status": "status=%s",
    }
    for key, sql in filters.items():
        value = request.args.get(key)
        if value:
            conditions.append(sql)
            params.append(f"%{value}%" if key == "city" else value)
    for param_name, sql in [
        ("collection_from", "collection_date >= %s"),
        ("collection_to", "collection_date <= %s"),
        ("expiry_from", "expiry_date >= %s"),
        ("expiry_to", "expiry_date <= %s"),
    ]:
        value = request.args.get(param_name)
        if value:
            conditions.append(sql)
            params.append(value)
    search = request.args.get("search")
    if search:
        conditions.append(
            "(CAST(id AS CHAR) LIKE %s OR donor_name LIKE %s OR donor_phone LIKE %s)"
        )
        term = f"%{search}%"
        params.extend([term, term, term])

    where = " WHERE " + " AND ".join(conditions) if conditions else ""
    count_params = list(params)
    total = fetch_one("SELECT COUNT(*) AS total FROM inventory" + where, tuple(count_params))["total"]
    allowed_sort = {
        "id": "id", "blood_group": "blood_group", "available_units": "available_units",
        "collection_date": "collection_date", "expiry_date": "expiry_date",
        "created_at": "created_at",
    }
    sort = allowed_sort.get(request.args.get("sort"), "created_at")
    direction = "ASC" if request.args.get("direction") == "asc" else "DESC"
    rows = fetch_all(
        "SELECT * FROM inventory" + where +
        f" ORDER BY {sort} {direction} LIMIT %s OFFSET %s",
        tuple(params + [per_page, offset]),
    )
    return jsonify(success=True, inventory=rows, total=total, page=page, per_page=per_page)


@inventory_bp.put("/api/inventory/<int:inventory_id>")
@jwt_required_dashboard
def update_inventory(inventory_id):
    data = request.get_json(silent=True) or {}
    try:
        available = int(data.get("available_units"))
    except (TypeError, ValueError):
        return jsonify(success=False, error="Available units must be an integer"), 400
    try:
        status = update_inventory_units(
            inventory_id,
            available,
            str(data.get("change_reason", "Available units updated")),
        )
        if status is None:
            return jsonify(success=False, error="Inventory batch not found"), 404
        return jsonify(success=True, status=status)
    except ValueError as exc:
        return jsonify(success=False, error=str(exc)), 400


@inventory_bp.get("/api/inventory/<int:inventory_id>")
@jwt_required_dashboard
def inventory_details(inventory_id):
    row = fetch_one("SELECT * FROM inventory WHERE id=%s", (inventory_id,))
    if not row:
        return jsonify(success=False, error="Inventory batch not found"), 404
    return jsonify(success=True, inventory=row)


@inventory_bp.post("/api/inventory/<int:inventory_id>/reserve")
@jwt_required_dashboard
def reserve_inventory(inventory_id):
    data = request.get_json(silent=True) or {}
    try:
        units = int(data.get("units", 0))
        conn = get_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM inventory WHERE id=%s FOR UPDATE", (inventory_id,))
        row = cursor.fetchone()
        if not row:
            conn.close()
            return jsonify(success=False, error="Inventory batch not found"), 404
        if units < 1 or units > row["available_units"]:
            conn.close()
            return jsonify(success=False, error="Reserved units exceed available stock"), 400
        previous_status = row["status"]
        available = row["available_units"] - units
        reserved = row["reserved_units"] + units
        status = "Reserved" if available == 0 else "Partially Reserved"
        cursor.execute(
            "UPDATE inventory SET available_units=%s,reserved_units=%s,status=%s,updated_at=CURRENT_TIMESTAMP WHERE id=%s",
            (available, reserved, status, inventory_id),
        )
        cursor.execute(
            "INSERT INTO inventory_history (inventory_id,previous_units,updated_units,previous_status,updated_status,change_reason) VALUES (%s,%s,%s,%s,%s,%s)",
            (inventory_id, row["available_units"], available, previous_status, status, "Units reserved"),
        )
        conn.commit()
        conn.close()
        return jsonify(success=True, status=status)
    except Exception:
        return jsonify(success=False, error="Could not reserve inventory"), 500


@inventory_bp.post("/api/inventory/<int:inventory_id>/unavailable")
@jwt_required_dashboard
def unavailable_inventory(inventory_id):
    try:
        status = update_inventory_units(inventory_id, 0, "Marked unavailable")
        if status is None:
            return jsonify(success=False, error="Inventory batch not found"), 404
        return jsonify(success=True, status=status)
    except ValueError as exc:
        return jsonify(success=False, error=str(exc)), 400


@inventory_bp.get("/api/inventory/history")
@jwt_required_dashboard
def history_api():
    rows = fetch_all(
        """
        SELECT h.*, i.blood_group, i.component_type
        FROM inventory_history h
        JOIN inventory i ON i.id=h.inventory_id
        ORDER BY h.changed_at DESC LIMIT 500
        """
    )
    return jsonify(success=True, history=rows)
