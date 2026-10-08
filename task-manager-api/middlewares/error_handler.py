import logging

from flask import jsonify

logger = logging.getLogger(__name__)


def register_error_handlers(app):
    @app.errorhandler(404)
    def handle_404(e):
        return jsonify({'error': 'Recurso não encontrado'}), 404

    @app.errorhandler(ValueError)
    def handle_value_error(e):
        return jsonify({'error': 'Dados inválidos'}), 400

    @app.errorhandler(Exception)
    def handle_unexpected(e):
        logger.exception('erro inesperado')
        return jsonify({'error': 'Erro interno do servidor'}), 500
