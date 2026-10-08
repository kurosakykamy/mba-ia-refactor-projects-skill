from database import db
from middlewares.auth import generate_token
from models.task import Task
from models.user import User
from utils.helpers import MIN_PASSWORD_LENGTH, VALID_ROLES, validate_email


def list_users():
    result = []
    for user in User.query.all():
        data = user.to_dict()
        data['task_count'] = len(user.tasks)
        result.append(data)
    return result


def get_user(user_id):
    user = User.query.get(user_id)
    if not user:
        return None
    data = user.to_dict()
    data['tasks'] = [t.to_dict() for t in Task.query.filter_by(user_id=user_id).all()]
    return data


def create_user(data):
    name = data.get('name')
    email = data.get('email')
    password = data.get('password')
    role = data.get('role', 'user')

    if not name:
        return None, 'Nome é obrigatório', 400
    if not email:
        return None, 'Email é obrigatório', 400
    if not password:
        return None, 'Senha é obrigatória', 400
    if not validate_email(email):
        return None, 'Email inválido', 400
    if len(password) < MIN_PASSWORD_LENGTH:
        return None, f'Senha deve ter no mínimo {MIN_PASSWORD_LENGTH} caracteres', 400
    if User.query.filter_by(email=email).first():
        return None, 'Email já cadastrado', 409
    if role not in VALID_ROLES:
        return None, 'Role inválido', 400

    user = User(name=name, email=email, role=role)
    user.set_password(password)

    db.session.add(user)
    db.session.commit()
    return user.to_dict(), None, 201


def update_user(user_id, data):
    user = User.query.get(user_id)
    if not user:
        return None, 'Usuário não encontrado', 404

    if 'name' in data:
        user.name = data['name']

    if 'email' in data:
        if not validate_email(data['email']):
            return None, 'Email inválido', 400
        existing = User.query.filter_by(email=data['email']).first()
        if existing and existing.id != user_id:
            return None, 'Email já cadastrado', 409
        user.email = data['email']

    if 'password' in data:
        if len(data['password']) < MIN_PASSWORD_LENGTH:
            return None, 'Senha muito curta', 400
        user.set_password(data['password'])

    if 'role' in data:
        if data['role'] not in VALID_ROLES:
            return None, 'Role inválido', 400
        user.role = data['role']

    if 'active' in data:
        user.active = data['active']

    db.session.commit()
    return user.to_dict(), None, 200


def delete_user(user_id):
    user = User.query.get(user_id)
    if not user:
        return False
    Task.query.filter_by(user_id=user_id).delete()
    db.session.delete(user)
    db.session.commit()
    return True


def get_user_tasks(user_id):
    user = User.query.get(user_id)
    if not user:
        return None
    return [t.to_dict() for t in Task.query.filter_by(user_id=user_id).all()]


def authenticate(email, password):
    if not email or not password:
        return None, 'Email e senha são obrigatórios', 400

    user = User.query.filter_by(email=email).first()
    if not user or not user.check_password(password):
        return None, 'Credenciais inválidas', 401

    if not user.active:
        return None, 'Usuário inativo', 403

    token = generate_token(user)
    return {'user': user.to_dict(), 'token': token}, None, 200
