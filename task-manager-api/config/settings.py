import os

from dotenv import load_dotenv

load_dotenv()

APP_ENV = os.environ.get("APP_ENV", "development")


def _required_secret(name, dev_default):
    """Fail-closed: fora de desenvolvimento, segredo ausente impede o boot.

    Um fallback silencioso faria a aplicação subir com a chave que está
    commitada no repositório — exatamente o problema que extrair para
    variável de ambiente deveria resolver. Como SECRET_KEY assina os tokens
    de autenticação (middlewares/auth.py), um default público permitiria a
    qualquer leitor do repositório forjar um token de admin.
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
    SQLALCHEMY_DATABASE_URI = os.environ.get("DATABASE_URL", "sqlite:///tasks.db")
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    DEBUG = os.environ.get("FLASK_DEBUG", "false").lower() == "true"
    HOST = os.environ.get("HOST", "0.0.0.0")
    PORT = int(os.environ.get("PORT", "5000"))
    CORS_ORIGINS = os.environ.get("CORS_ORIGINS", "http://localhost:3000").split(",")

    SMTP_HOST = os.environ.get("SMTP_HOST", "smtp.gmail.com")
    SMTP_PORT = int(os.environ.get("SMTP_PORT", "587"))
    SMTP_USER = os.environ.get("SMTP_USER", "taskmanager@example.com")
    SMTP_PASSWORD = _required_secret("SMTP_PASSWORD", "dev-only-change-me")
