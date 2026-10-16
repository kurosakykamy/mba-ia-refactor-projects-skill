import logging

from flask import jsonify
from werkzeug.exceptions import HTTPException

logger = logging.getLogger(__name__)


class AppError(Exception):
    """Exceção de domínio. Subclasses são traduzidas em resposta HTTP pelo
    handler central — camadas de negócio levantam, não formatam resposta."""

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
        # ValueError costuma ser bug de programação — logar antes de devolver 400,
        # senão o erro desaparece sem rastro.
        logger.exception("ValueError tratado como requisição inválida")
        return jsonify({"erro": "Dados inválidos", "sucesso": False}), 400

    @app.errorhandler(HTTPException)
    def handle_http_exception(e):
        # Preserva o status correto (405, 415, 400...) em vez de deixar o
        # catch-all de Exception converter tudo em 500.
        return jsonify({"erro": e.description, "sucesso": False}), e.code

    @app.errorhandler(Exception)
    def handle_unexpected(e):
        logger.exception("erro inesperado")
        return jsonify({"erro": "Erro interno do servidor", "sucesso": False}), 500
