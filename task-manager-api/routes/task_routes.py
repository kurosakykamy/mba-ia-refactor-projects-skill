from flask import Blueprint, jsonify, request

from controllers import task_controller
from middlewares.auth import login_required

task_bp = Blueprint('tasks', __name__)


@task_bp.route('/tasks', methods=['GET'])
@login_required
def get_tasks():
    return jsonify(task_controller.list_tasks()), 200


@task_bp.route('/tasks/<int:task_id>', methods=['GET'])
@login_required
def get_task(task_id):
    task = task_controller.get_task(task_id)
    if not task:
        return jsonify({'error': 'Task não encontrada'}), 404
    return jsonify(task), 200


@task_bp.route('/tasks', methods=['POST'])
@login_required
def create_task():
    data = request.get_json(silent=True) or {}
    task, error, status = task_controller.create_task(data)
    if error:
        return jsonify({'error': error}), status
    return jsonify(task), status


@task_bp.route('/tasks/<int:task_id>', methods=['PUT'])
@login_required
def update_task(task_id):
    data = request.get_json(silent=True) or {}
    task, error, status = task_controller.update_task(task_id, data)
    if error:
        return jsonify({'error': error}), status
    return jsonify(task), status


@task_bp.route('/tasks/<int:task_id>', methods=['DELETE'])
@login_required
def delete_task(task_id):
    if not task_controller.delete_task(task_id):
        return jsonify({'error': 'Task não encontrada'}), 404
    return jsonify({'message': 'Task deletada com sucesso'}), 200


@task_bp.route('/tasks/search', methods=['GET'])
@login_required
def search_tasks():
    query = request.args.get('q', '')
    status = request.args.get('status', '')
    priority_raw = request.args.get('priority', '')
    user_id_raw = request.args.get('user_id', '')

    try:
        priority = int(priority_raw) if priority_raw else None
        user_id = int(user_id_raw) if user_id_raw else None
    except ValueError:
        return jsonify({'error': 'priority e user_id devem ser numéricos'}), 400

    return jsonify(task_controller.search_tasks(query, status, priority, user_id)), 200


@task_bp.route('/tasks/stats', methods=['GET'])
@login_required
def task_stats():
    return jsonify(task_controller.task_stats()), 200
