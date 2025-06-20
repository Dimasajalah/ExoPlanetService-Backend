from flask import Blueprint, jsonify, request
from utils.verify_user import verify_token
from models.user_model import find_user_by_id, update_user, delete_user
from extensions import mongo

user_bp = Blueprint('user', __name__, url_prefix='/api/user')

@user_bp.route('/test', methods=['GET'])
def test():
    return jsonify({"message": "API route is working!"})

@user_bp.route('/update/<user_id>', methods=['POST'])
@verify_token
def update_user_route(user_id):
    # ✅ pastikan id dari token cocok dengan user_id URL
    if str(request.user.get('id')) != str(user_id):
        return jsonify({"error": "You can only update your own account!"}), 401

    data = request.json
    if 'password' in data:
        from werkzeug.security import generate_password_hash
        data['password'] = generate_password_hash(data['password'])

    update_user(mongo, user_id, data)
    user = find_user_by_id(mongo, user_id)
    if user:
        user['_id'] = str(user['_id'])
        user.pop('password', None)
        return jsonify(user), 200
    else:
        return jsonify({"error": "User not found"}), 404

@user_bp.route('/delete/<user_id>', methods=['DELETE'])
@verify_token
def delete_user_route(user_id):
    if str(request.user.get('id')) != str(user_id):
        return jsonify({"error": "You can only delete your own account!"}), 401

    delete_user(mongo, user_id)
    resp = jsonify({"message": "User has been deleted!"})
    resp.delete_cookie('access_token')
    return resp, 200

@user_bp.route('/me', methods=['GET'])
@verify_token
def get_current_user():
    user = find_user_by_id(mongo, request.user.get('id'))
    if user:
        user['_id'] = str(user['_id'])
        user.pop('password', None)
        return jsonify(user), 200
    else:
        return jsonify({"error": "User not found"}), 404

@user_bp.route('/all', methods=['GET'])
def get_all_users():
    try:
        users = list(mongo.db.users.find({}, {"password": 0}))
        for user in users:
            user['_id'] = str(user['_id'])
        return jsonify(users), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500
