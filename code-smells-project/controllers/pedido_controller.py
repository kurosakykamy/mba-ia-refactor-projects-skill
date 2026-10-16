from flask import jsonify, request

from config.settings import Settings
from models import pedido_model
from services import notification_service, pedido_service, relatorio_service


def criar_pedido():
    dados = request.get_json(silent=True) or {}
    usuario_id = dados.get("usuario_id")
    itens = dados.get("itens", [])

    if not usuario_id:
        return jsonify({"erro": "Usuario ID é obrigatório"}), 400
    if not itens:
        return jsonify({"erro": "Pedido deve ter pelo menos 1 item"}), 400

    # Erros de domínio sobem como AppError e são traduzidos pelo handler central.
    # A notificação é disparada dentro do service, junto da regra que a origina.
    resultado = pedido_service.criar_pedido(usuario_id, itens)
    return jsonify({"dados": resultado, "sucesso": True, "mensagem": "Pedido criado com sucesso"}), 201


def listar_pedidos_usuario(usuario_id):
    return jsonify({"dados": pedido_model.get_por_usuario(usuario_id), "sucesso": True}), 200


def listar_todos_pedidos():
    return jsonify({"dados": pedido_model.get_todos(), "sucesso": True}), 200


def atualizar_status_pedido(pedido_id):
    dados = request.get_json(silent=True) or {}
    novo_status = dados.get("status", "")

    if novo_status not in Settings.STATUS_PEDIDO_VALIDOS:
        return jsonify({"erro": "Status inválido"}), 400
    if not pedido_model.existe(pedido_id):
        return jsonify({"erro": "Pedido não encontrado"}), 404

    pedido_model.atualizar_status(pedido_id, novo_status)
    notification_service.notificar_status_pedido(pedido_id, novo_status)
    return jsonify({"sucesso": True, "mensagem": "Status atualizado"}), 200


def relatorio_vendas():
    return jsonify({"dados": relatorio_service.gerar_relatorio_vendas(), "sucesso": True}), 200
