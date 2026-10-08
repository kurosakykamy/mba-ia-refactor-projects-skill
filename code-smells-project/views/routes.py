from flask import Blueprint

from controllers import pedido_controller, produto_controller, sistema_controller, usuario_controller

produtos_bp = Blueprint("produtos", __name__)
produtos_bp.add_url_rule("/produtos", view_func=produto_controller.listar_produtos, methods=["GET"])
produtos_bp.add_url_rule("/produtos/busca", view_func=produto_controller.buscar_produtos, methods=["GET"])
produtos_bp.add_url_rule("/produtos/<int:id>", view_func=produto_controller.buscar_produto, methods=["GET"])
produtos_bp.add_url_rule("/produtos", view_func=produto_controller.criar_produto, methods=["POST"])
produtos_bp.add_url_rule("/produtos/<int:id>", view_func=produto_controller.atualizar_produto, methods=["PUT"])
produtos_bp.add_url_rule("/produtos/<int:id>", view_func=produto_controller.deletar_produto, methods=["DELETE"])

usuarios_bp = Blueprint("usuarios", __name__)
usuarios_bp.add_url_rule("/usuarios", view_func=usuario_controller.listar_usuarios, methods=["GET"])
usuarios_bp.add_url_rule("/usuarios/<int:id>", view_func=usuario_controller.buscar_usuario, methods=["GET"])
usuarios_bp.add_url_rule("/usuarios", view_func=usuario_controller.criar_usuario, methods=["POST"])
usuarios_bp.add_url_rule("/login", view_func=usuario_controller.login, methods=["POST"])

pedidos_bp = Blueprint("pedidos", __name__)
pedidos_bp.add_url_rule("/pedidos", view_func=pedido_controller.criar_pedido, methods=["POST"])
pedidos_bp.add_url_rule("/pedidos", view_func=pedido_controller.listar_todos_pedidos, methods=["GET"])
pedidos_bp.add_url_rule(
    "/pedidos/usuario/<int:usuario_id>", view_func=pedido_controller.listar_pedidos_usuario, methods=["GET"]
)
pedidos_bp.add_url_rule(
    "/pedidos/<int:pedido_id>/status", view_func=pedido_controller.atualizar_status_pedido, methods=["PUT"]
)
pedidos_bp.add_url_rule("/relatorios/vendas", view_func=pedido_controller.relatorio_vendas, methods=["GET"])

sistema_bp = Blueprint("sistema", __name__)
sistema_bp.add_url_rule("/health", view_func=sistema_controller.health_check, methods=["GET"])
sistema_bp.add_url_rule("/", view_func=sistema_controller.index, methods=["GET"])


def register_routes(app):
    app.register_blueprint(produtos_bp)
    app.register_blueprint(usuarios_bp)
    app.register_blueprint(pedidos_bp)
    app.register_blueprint(sistema_bp)
