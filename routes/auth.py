from flask import Blueprint, request, jsonify
from werkzeug.security import check_password_hash, generate_password_hash
from flask_jwt_extended import create_access_token
from extensions import mongo

auth_blueprint = Blueprint("auth", __name__)  # Changed from auth_bp to auth_blueprint

@auth_blueprint.route("/register", methods=["POST"])
def register():
    data = request.json
    user = mongo.db.users.find_one({"username": data["username"]})
    if user:
        return jsonify({"msg": "Username already exists"}), 409

    new_user = {
        "username": data["username"],
        "password": generate_password_hash(data["password"])
    }
    mongo.db.users.insert_one(new_user)
    return jsonify({"msg": "User registered successfully"})

@auth_blueprint.route("/login", methods=["POST"])
def login():
    data = request.json
    user = mongo.db.users.find_one({"username": data["username"]})
    if not user or not check_password_hash(user["password"], data["password"]):
        return jsonify({"msg": "Invalid credentials"}), 401

    token = create_access_token(identity=user["username"])
    return jsonify(access_token=token)