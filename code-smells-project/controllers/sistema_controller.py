from flask import jsonify

from database import get_db


def health_check():
    db = get_db()
    produtos = db.execute("SELECT COUNT(*) FROM produtos").fetchone()[0]
    usuarios = db.execute("SELECT COUNT(*) FROM usuarios").fetchone()[0]
    pedidos = db.execute("SELECT COUNT(*) FROM pedidos").fetchone()[0]

    return jsonify(
        {
            "status": "ok",
            "database": "connected",
            "counts": {"produtos": produtos, "usuarios": usuarios, "pedidos": pedidos},
            "versao": "1.0.0",
        }
    ), 200


def index():
    return jsonify(
        {
            "mensagem": "Bem-vindo à API da Loja",
            "versao": "1.0.0",
            "endpoints": {
                "produtos": "/produtos",
                "usuarios": "/usuarios",
                "pedidos": "/pedidos",
                "login": "/login",
                "relatorios": "/relatorios/vendas",
                "health": "/health",
            },
        }
    )
