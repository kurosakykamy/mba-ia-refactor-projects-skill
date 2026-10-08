import os


class Settings:
    SECRET_KEY = os.environ.get("SECRET_KEY", "dev-only-insecure-key-change-me")
    DEBUG = os.environ.get("FLASK_DEBUG", "false").lower() == "true"
    DATABASE_PATH = os.environ.get("DATABASE_PATH", "loja.db")
    HOST = os.environ.get("HOST", "0.0.0.0")
    PORT = int(os.environ.get("PORT", "5000"))
    CORS_ORIGINS = os.environ.get("CORS_ORIGINS", "http://localhost:3000").split(",")

    CATEGORIAS_VALIDAS = ["informatica", "moveis", "vestuario", "geral", "eletronicos", "livros"]
    STATUS_PEDIDO_VALIDOS = ["pendente", "aprovado", "enviado", "entregue", "cancelado"]

    LIMITE_FAIXA_ALTA = 10_000
    DESCONTO_FAIXA_ALTA = 0.10
    LIMITE_FAIXA_MEDIA = 5_000
    DESCONTO_FAIXA_MEDIA = 0.05
    LIMITE_FAIXA_BAIXA = 1_000
    DESCONTO_FAIXA_BAIXA = 0.02
