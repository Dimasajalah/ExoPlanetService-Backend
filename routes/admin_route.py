# routes/admin_route.py (lanjutan dan perbaikan)
from flask import Blueprint, jsonify, request
from utils.verify_admin import verify_admin
from extensions import mongo
from bson.objectid import ObjectId
from datetime import datetime

admin_bp = Blueprint("admin", __name__, url_prefix="/api/admin")

# ✅ GET semua pengguna tanpa password
@admin_bp.route("/users", methods=["GET"])
@verify_admin
def get_all_users_admin():
    users = list(mongo.db.users.find({}, {"password": 0}))
    for user in users:
        user["_id"] = str(user["_id"])
    return jsonify(users), 200

# ✅ PATCH Role user
@admin_bp.route("/user/<user_id>/role", methods=["PATCH"])
@verify_admin
def update_user_role(user_id):
    data = request.json
    new_role = data.get("role")
    if new_role not in ["user", "admin"]:
        return jsonify({"error": "Invalid role"}), 400
    result = mongo.db.users.update_one(
        {"_id": ObjectId(user_id)},
        {"$set": {"role": new_role}}
    )
    log_admin_action("update-role", user_id, f"Set role to {new_role}")
    return jsonify({"message": "Role updated"}), 200

# ✅ DELETE User by Admin
@admin_bp.route("/user/<user_id>", methods=["DELETE"])
@verify_admin
def delete_user_by_admin(user_id):
    mongo.db.users.delete_one({"_id": ObjectId(user_id)})
    log_admin_action("delete-user", user_id, "Deleted user")
    return jsonify({"message": "User deleted by admin"}), 200

# ✅ Statistik: total user, pesan, dataset
@admin_bp.route("/stats", methods=["GET"])
@verify_admin
def get_admin_stats():
    user_count = mongo.db.users.count_documents({})
    message_count = mongo.db.contacts.count_documents({})
    dataset_count = mongo.db.exoplanets.count_documents({})

    role_dist = mongo.db.users.aggregate([
        {"$group": {"_id": "$role", "value": {"$sum": 1}}},
    ])

    # Aktivitas kontak selama 7 hari terakhir
    from datetime import datetime, timedelta
    days = [datetime.utcnow() - timedelta(days=i) for i in range(6, -1, -1)]
    activity = []
    for day in days:
        next_day = day + timedelta(days=1)
        count = mongo.db.contacts.count_documents({
            "timestamp": {"$gte": day, "$lt": next_day}
        })
        activity.append({"date": day.strftime('%Y-%m-%d'), "count": count})

    return jsonify({
        "totalUsers": user_count,
        "totalMessages": message_count,
        "totalDatasets": dataset_count,
        "userRoles": list(role_dist),
        "contactActivity": activity
    }), 200

# ✅ Settings GET + PUT (1 dokumen tunggal)
@admin_bp.route("/settings", methods=["GET"])
@verify_admin
def get_settings():
    settings = mongo.db.settings.find_one({})
    if settings:
        settings["_id"] = str(settings["_id"])
    return jsonify(settings or {}), 200

@admin_bp.route("/settings", methods=["PUT"])
@verify_admin
def update_settings():
    data = request.json
    mongo.db.settings.update_one({}, {"$set": data}, upsert=True)
    log_admin_action("update-settings", "all", str(data))
    return jsonify({"message": "Settings updated"}), 200

# ✅ Log aktivitas admin
@admin_bp.route("/audit-trail", methods=["GET"])
@verify_admin
def get_audit_trail():
    logs = list(mongo.db.audit_logs.find().sort("timestamp", -1).limit(100))
    for log in logs:
        log["_id"] = str(log["_id"])
        log["timestamp"] = log["timestamp"].isoformat()
    return jsonify(logs), 200

# 🔧 Fungsi internal log

def log_admin_action(action, target_id, description):
    mongo.db.audit_logs.insert_one({
        "action": action,
        "target_id": str(target_id),
        "description": description,
        "performed_by": getattr(request, 'user', {}).get("id", "unknown"),
        "timestamp": datetime.utcnow(),
    })
