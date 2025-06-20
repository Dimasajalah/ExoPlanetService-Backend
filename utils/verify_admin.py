from flask import request, jsonify
from functools import wraps
import jwt
import os

def verify_admin(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = request.cookies.get('access_token')
        if not token:
            return jsonify({"error": "Unauthorized"}), 401
        try:
            decoded = jwt.decode(token, os.environ.get("JWT_SECRET", "secret"), algorithms=["HS256"])
            from extensions import mongo
            user = mongo.db.users.find_one({"_id": decoded["id"]})
            if not user or user.get("role") != "admin":
                return jsonify({"error": "Forbidden. Admin only."}), 403
            request.user = {"id": str(user["_id"]), "role": user["role"]}
        except Exception as e:
            return jsonify({"error": "Invalid token"}), 403
        return f(*args, **kwargs)
    return decorated
