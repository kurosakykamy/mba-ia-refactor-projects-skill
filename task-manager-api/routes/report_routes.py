from flask import Blueprint, jsonify, request

from controllers import category_controller, report_controller
from middlewares.auth import admin_required, login_required

report_bp = Blueprint('reports', __name__)


@report_bp.route('/reports/summary', methods=['GET'])
@login_required
def summary_report():
    return jsonify(report_controller.summary_report()), 200


@report_bp.route('/reports/user/<int:user_id>', methods=['GET'])
@login_required
def user_report(user_id):
    report = report_controller.user_report(user_id)
    if not report:
        return jsonify({'error': 'Usuário não encontrado'}), 404
    return jsonify(report), 200


@report_bp.route('/categories', methods=['GET'])
@login_required
def get_categories():
    return jsonify(category_controller.list_categories()), 200


@report_bp.route('/categories', methods=['POST'])
@admin_required
def create_category():
    data = request.get_json(silent=True) or {}
    category, error, status = category_controller.create_category(data)
    if error:
        return jsonify({'error': error}), status
    return jsonify(category), status


@report_bp.route('/categories/<int:cat_id>', methods=['PUT'])
@admin_required
def update_category(cat_id):
    data = request.get_json(silent=True) or {}
    category, error, status = category_controller.update_category(cat_id, data)
    if error:
        return jsonify({'error': error}), status
    return jsonify(category), status


@report_bp.route('/categories/<int:cat_id>', methods=['DELETE'])
@admin_required
def delete_category(cat_id):
    if not category_controller.delete_category(cat_id):
        return jsonify({'error': 'Categoria não encontrada'}), 404
    return jsonify({'message': 'Categoria deletada'}), 200
