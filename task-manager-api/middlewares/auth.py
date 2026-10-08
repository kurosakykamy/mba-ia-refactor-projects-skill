from functools import wraps

from flask import current_app, jsonify, request
from itsdangerous import BadSignature, SignatureExpired, URLSafeTimedSerializer

from models.user import User

TOKEN_MAX_AGE_SECONDS = 60 * 60 * 24


def generate_token(user):
    serializer = URLSafeTimedSerializer(current_app.config['SECRET_KEY'])
    return serializer.dumps({'user_id': user.id})


def _resolve_user_from_request():
    auth_header = request.headers.get('Authorization', '')
    if not auth_header.startswith('Bearer '):
        return None
    token = auth_header[len('Bearer '):]
    serializer = URLSafeTimedSerializer(current_app.config['SECRET_KEY'])
    try:
        data = serializer.loads(token, max_age=TOKEN_MAX_AGE_SECONDS)
    except (BadSignature, SignatureExpired):
        return None
    return User.query.get(data.get('user_id'))


def login_required(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        user = _resolve_user_from_request()
        if not user:
            return jsonify({'error': 'unauthorized'}), 401
        request.current_user = user
        return fn(*args, **kwargs)
    return wrapper


def admin_required(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        user = _resolve_user_from_request()
        if not user:
            return jsonify({'error': 'unauthorized'}), 401
        if not user.is_admin():
            return jsonify({'error': 'forbidden'}), 403
        request.current_user = user
        return fn(*args, **kwargs)
    return wrapper
