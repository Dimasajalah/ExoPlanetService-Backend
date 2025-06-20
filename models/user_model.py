from flask_pymongo import PyMongo
from werkzeug.security import generate_password_hash, check_password_hash
from bson.objectid import ObjectId  # <-- harus import ini

def get_user_collection(mongo):
    return mongo.db.users

def create_user(mongo, username, email, password, avatar=None, role='user'):
    user = {
        "username": username,
        "email": email,
        "password": generate_password_hash(password),
        "avatar": avatar or "https://cdn.pixabay.com/photo/2015/10/05/22/37/blank-profile-picture-973460_1280.png",
        "role": role  # Tambahkan field role
    }
    return mongo.db.users.insert_one(user)

def find_user_by_email(mongo, email):
    return mongo.db.users.find_one({"email": email})

def find_user_by_id(mongo, user_id):
    try:
        oid = ObjectId(user_id)  # <-- convert string ke ObjectId
    except:
        return None
    return mongo.db.users.find_one({"_id": oid})

def update_user(mongo, user_id, data):
    try:
        oid = ObjectId(user_id)
    except:
        return None
    return mongo.db.users.update_one({"_id": oid}, {"$set": data})

def delete_user(mongo, user_id):
    try:
        oid = ObjectId(user_id)
    except:
        return None
    return mongo.db.users.delete_one({"_id": oid})




