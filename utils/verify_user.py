from functools import wraps
from flask import request, jsonify
import jwt
import os

def verify_token(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        # ✅ 1. Ambil token dari cookie
        token = request.cookies.get('access_token')

        # ✅ 2. Jika token tidak ada di cookie, coba ambil dari header Authorization
        if not token:
            auth_header = request.headers.get('Authorization')
            if auth_header and auth_header.startswith('Bearer '):
                token = auth_header.split(' ')[1]

        # ✅ 3. Jika masih tidak ada, balas unauthorized
        if not token:
            return jsonify({"error": "Unauthorized"}), 401

        try:
            user = jwt.decode(token, os.environ.get("JWT_SECRET", "secret"), algorithms=["HS256"])
            request.user = user
        except Exception:
            return jsonify({"error": "Forbidden"}), 403

        return f(*args, **kwargs)
    return decorated
