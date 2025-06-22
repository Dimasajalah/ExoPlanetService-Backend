from flask import Blueprint, request, jsonify, make_response
from flask_cors import cross_origin
from models.user_model import create_user, find_user_by_email
from utils.error import error_handler
from werkzeug.security import check_password_hash
from extensions import mongo
import jwt
import os
import datetime

auth_bp = Blueprint('auth', __name__, url_prefix='/api/auth')

# Frontend origin yang diizinkan
FRONTEND_URL = "https://exo-planet-service-frontend-n5ig-5cmpfimi1.vercel.app"

# 🔹 GOOGLE LOGIN
@auth_bp.route('/google', methods=['POST'])
@cross_origin(
    origins=FRONTEND_URL,
    supports_credentials=True,
    methods=["POST"],
    allow_headers=["Content-Type"]
)
def google_login():
    data = request.get_json()
    email = data.get('email')
    name = data.get('name')
    avatar = data.get('photo')

    if not email or not name:
        return error_handler(400, "Email dan nama diperlukan")

    user = find_user_by_email(mongo, email)

    if not user:
        create_user(
            mongo,
            username=name,
            email=email,
            password="",
            avatar=avatar,
            role='user'
        )
        user = find_user_by_email(mongo, email)

    token = jwt.encode(
        {"id": str(user['_id']), "exp": datetime.datetime.utcnow() + datetime.timedelta(hours=24)},
        os.environ.get("JWT_SECRET", "secret"),
        algorithm="HS256"
    )

    user_response = {
        "_id": str(user["_id"]),
        "username": user.get("username"),
        "email": user.get("email"),
        "avatar": user.get("avatar"),
        "role": user.get("role", "user")
    }

    resp = make_response(jsonify(user_response))
    resp.set_cookie(
        'access_token',
        token,
        httponly=True,
        secure=True,
        samesite='None'
    )
    return resp, 200


# 🔹 SIGN UP
@auth_bp.route('/signup', methods=['POST'])
@cross_origin(
    origins=FRONTEND_URL,
    supports_credentials=True,
    methods=["POST"],
    allow_headers=["Content-Type"]
)
def signup():
    data = request.json
    email = data.get('email')
    username = data.get('username')
    password = data.get('password')
    role = data.get('role', 'user')

    if not all([email, username, password]):
        return error_handler(400, "Email, username, dan password wajib diisi")

    if find_user_by_email(mongo, email):
        return error_handler(400, "User already exists")

    create_user(mongo, username=username, email=email, password=password, role=role)
    user = find_user_by_email(mongo, email)

    token = jwt.encode(
        {"id": str(user['_id']), "exp": datetime.datetime.utcnow() + datetime.timedelta(hours=24)},
        os.environ.get("JWT_SECRET", "secret"),
        algorithm="HS256"
    )

    user_response = {
        "_id": str(user["_id"]),
        "username": user.get("username"),
        "email": user.get("email"),
        "avatar": user.get("avatar"),
        "role": user.get("role", "user")
    }

    resp = make_response(jsonify(user_response))
    resp.set_cookie(
        'access_token',
        token,
        httponly=True,
        secure=True,
        samesite='None'
    )
    return resp, 201


# 🔹 SIGN IN
@auth_bp.route('/signin', methods=['POST'])
@cross_origin(
    origins=FRONTEND_URL,
    supports_credentials=True,
    methods=["POST"],
    allow_headers=["Content-Type"]
)
def signin():
    data = request.json
    email = data.get('email')
    password = data.get('password')

    if not email or not password:
        return error_handler(400, "Email dan password wajib diisi")

    user = find_user_by_email(mongo, email)
    if not user:
        return error_handler(404, "User not found!")

    if not check_password_hash(user['password'], password):
        return error_handler(401, "Wrong credentials!")

    token = jwt.encode(
        {"id": str(user['_id']), "exp": datetime.datetime.utcnow() + datetime.timedelta(hours=24)},
        os.environ.get("JWT_SECRET", "secret"),
        algorithm="HS256"
    )

    user_response = {
        "_id": str(user["_id"]),
        "username": user.get("username"),
        "email": user.get("email"),
        "avatar": user.get("avatar"),
        "role": user.get("role", "user")
    }

    resp = make_response(jsonify(user_response))
    resp.set_cookie(
        'access_token',
        token,
        httponly=True,
        secure=True,
        samesite='None'
    )
    return resp, 200


# 🔹 SIGN OUT
@auth_bp.route('/signout', methods=['GET'])
@cross_origin(
    origins=FRONTEND_URL,
    supports_credentials=True,
    methods=["GET"]
)
def signout():
    resp = jsonify({"message": "User has been logged out!"})
    resp.delete_cookie('access_token')
    return resp, 200
