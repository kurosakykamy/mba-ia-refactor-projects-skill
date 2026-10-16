import os

APP_ENV = os.environ.get("APP_ENV", "development")


def _required_secret(name, dev_default):
    """Fail-closed: fora de desenvolvimento, segredo ausente impede o boot.

    Um fallback silencioso faria a aplicação subir com a chave que está
    commitada no repositório — exatamente o problema que extrair para
    variável de ambiente deveria resolver.
    """
    value = os.environ.get(name)
    if value:
        return value
    if APP_ENV != "development":
        raise RuntimeError(
            f"{name} é obrigatório quando APP_ENV={APP_ENV}. "
            "Defina a variável de ambiente antes de subir a aplicação."
        )
    return dev_default


class Settings:
    APP_ENV = APP_ENV
    SECRET_KEY = _required_secret("SECRET_KEY", "dev-only-insecure-key-change-me")
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
