import logging

from flask import jsonify

logger = logging.getLogger(__name__)


class AppError(Exception):
    status_code = 400

    def __init__(self, message, status_code=None):
        super().__init__(message)
        self.message = message
        if status_code is not None:
            self.status_code = status_code


def register_error_handlers(app):
    @app.errorhandler(AppError)
    def handle_app_error(e):
        return jsonify({"erro": e.message, "sucesso": False}), e.status_code

    @app.errorhandler(404)
    def handle_404(e):
        return jsonify({"erro": "Recurso não encontrado", "sucesso": False}), 404

    @app.errorhandler(ValueError)
    def handle_value_error(e):
        return jsonify({"erro": "Dados inválidos", "sucesso": False}), 400

    @app.errorhandler(Exception)
    def handle_unexpected(e):
        logger.exception("erro inesperado")
        return jsonify({"erro": "Erro interno do servidor", "sucesso": False}), 500
