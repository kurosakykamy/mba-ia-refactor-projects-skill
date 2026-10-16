from flask import Blueprint, jsonify, request

from controllers import user_controller
from middlewares.auth import admin_required, login_required, resolve_optional_user

user_bp = Blueprint('users', __name__)


def _can_act_on(user_id):
    """Um usuário só age sobre si mesmo; admin age sobre qualquer um."""
    current = request.current_user
    return current.id == user_id or current.is_admin()


@user_bp.route('/users', methods=['GET'])
@admin_required
def get_users():
    return jsonify(user_controller.list_users()), 200


@user_bp.route('/users/<int:user_id>', methods=['GET'])
@login_required
def get_user(user_id):
    user = user_controller.get_user(user_id)
    if not user:
        return jsonify({'error': 'Usuário não encontrado'}), 404
    return jsonify(user), 200


@user_bp.route('/users', methods=['POST'])
def create_user():
    """Cadastro público: o `role` enviado pelo cliente é ignorado (sempre 'user').
    Criar usuário com papel elevado exige um token de admin."""
    data = request.get_json(silent=True) or {}
    requester = resolve_optional_user()
    is_admin = requester is not None and requester.is_admin()

    if 'role' in data and data['role'] != 'user' and not is_admin:
        return jsonify({'error': 'Apenas administradores podem definir o papel do usuário'}), 403

    user, error, status = user_controller.create_user(data, allow_role_assignment=is_admin)
    if error:
        return jsonify({'error': error}), status
    return jsonify(user), status


@user_bp.route('/users/<int:user_id>', methods=['PUT'])
@login_required
def update_user(user_id):
    data = request.get_json(silent=True) or {}
    if not _can_act_on(user_id):
        return jsonify({'error': 'forbidden'}), 403
    if 'role' in data and not request.current_user.is_admin():
        return jsonify({'error': 'Apenas administradores podem alterar o papel do usuário'}), 403
    user, error, status = user_controller.update_user(user_id, data)
    if error:
        return jsonify({'error': error}), status
    return jsonify(user), status


@user_bp.route('/users/<int:user_id>', methods=['DELETE'])
@admin_required
def delete_user(user_id):
    if not user_controller.delete_user(user_id):
        return jsonify({'error': 'Usuário não encontrado'}), 404
    return jsonify({'message': 'Usuário deletado com sucesso'}), 200


@user_bp.route('/users/<int:user_id>/tasks', methods=['GET'])
@login_required
def get_user_tasks(user_id):
    tasks = user_controller.get_user_tasks(user_id)
    if tasks is None:
        return jsonify({'error': 'Usuário não encontrado'}), 404
    return jsonify(tasks), 200


@user_bp.route('/login', methods=['POST'])
def login():
    data = request.get_json(silent=True) or {}
    result, error, status = user_controller.authenticate(data.get('email'), data.get('password'))
    if error:
        return jsonify({'error': error}), status
    return jsonify({'message': 'Login realizado com sucesso', **result}), status
