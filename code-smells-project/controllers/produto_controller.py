import logging

from flask import jsonify, request

from models import produto_model
from utils.validators import validar_produto

logger = logging.getLogger(__name__)


def listar_produtos():
    produtos = produto_model.get_todos()
    return jsonify({"dados": produtos, "sucesso": True}), 200


def buscar_produto(id):
    produto = produto_model.get_por_id(id)
    if not produto:
        return jsonify({"erro": "Produto não encontrado", "sucesso": False}), 404
    return jsonify({"dados": produto, "sucesso": True}), 200


def criar_produto():
    dados = request.get_json(silent=True) or {}
    erros = validar_produto(dados)
    if erros:
        return jsonify({"erro": erros[0], "erros": erros}), 400

    produto_id = produto_model.criar(
        dados["nome"],
        dados.get("descricao", ""),
        float(dados["preco"]),
        int(dados["estoque"]),
        dados.get("categoria", "geral"),
    )
    logger.info("produto.criado produto_id=%s", produto_id)
    return jsonify({"dados": {"id": produto_id}, "sucesso": True, "mensagem": "Produto criado"}), 201


def atualizar_produto(id):
    if not produto_model.get_por_id(id):
        return jsonify({"erro": "Produto não encontrado"}), 404

    dados = request.get_json(silent=True) or {}
    erros = validar_produto(dados)
    if erros:
        return jsonify({"erro": erros[0], "erros": erros}), 400

    produto_model.atualizar(
        id,
        dados["nome"],
        dados.get("descricao", ""),
        float(dados["preco"]),
        int(dados["estoque"]),
        dados.get("categoria", "geral"),
    )
    return jsonify({"sucesso": True, "mensagem": "Produto atualizado"}), 200


def deletar_produto(id):
    if not produto_model.get_por_id(id):
        return jsonify({"erro": "Produto não encontrado"}), 404

    produto_model.deletar(id)
    return jsonify({"sucesso": True, "mensagem": "Produto deletado"}), 200


def buscar_produtos():
    termo = request.args.get("q", "")
    categoria = request.args.get("categoria") or None
    preco_min = request.args.get("preco_min")
    preco_max = request.args.get("preco_max")
    preco_min = float(preco_min) if preco_min else None
    preco_max = float(preco_max) if preco_max else None

    resultados = produto_model.buscar(termo, categoria, preco_min, preco_max)
    return jsonify({"dados": resultados, "total": len(resultados), "sucesso": True}), 200
