import logging

from flask import jsonify, request

from models import usuario_model

logger = logging.getLogger(__name__)


def listar_usuarios():
    return jsonify({"dados": usuario_model.get_todos(), "sucesso": True}), 200


def buscar_usuario(id):
    usuario = usuario_model.get_por_id(id)
    if not usuario:
        return jsonify({"erro": "Usuário não encontrado"}), 404
    return jsonify({"dados": usuario, "sucesso": True}), 200


def criar_usuario():
    dados = request.get_json(silent=True) or {}
    nome = dados.get("nome", "")
    email = dados.get("email", "")
    senha = dados.get("senha", "")

    if not nome or not email or not senha:
        return jsonify({"erro": "Nome, email e senha são obrigatórios"}), 400

    usuario_id = usuario_model.criar(nome, email, senha)
    logger.info("usuario.criado usuario_id=%s", usuario_id)
    return jsonify({"dados": {"id": usuario_id}, "sucesso": True}), 201


def login():
    dados = request.get_json(silent=True) or {}
    email = dados.get("email", "")
    senha = dados.get("senha", "")

    if not email or not senha:
        return jsonify({"erro": "Email e senha são obrigatórios"}), 400

    usuario = usuario_model.autenticar(email, senha)
    if not usuario:
        logger.info("login.falhou")
        return jsonify({"erro": "Email ou senha inválidos", "sucesso": False}), 401

    logger.info("login.sucesso usuario_id=%s", usuario["id"])
    return jsonify({"dados": usuario, "sucesso": True, "mensagem": "Login OK"}), 200
