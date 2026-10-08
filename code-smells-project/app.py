import logging

from flask import Flask
from flask_cors import CORS

from config.settings import Settings
from database import init_db, register_db
from middlewares.error_handler import register_error_handlers
from views.routes import register_routes

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s %(message)s")
logger = logging.getLogger(__name__)


def create_app():
    app = Flask(__name__)
    app.config["SECRET_KEY"] = Settings.SECRET_KEY
    app.config["DEBUG"] = Settings.DEBUG

    CORS(app, origins=Settings.CORS_ORIGINS)

    register_db(app)
    register_routes(app)
    register_error_handlers(app)

    return app


app = create_app()

if __name__ == "__main__":
    init_db()
    logger.info("Servidor iniciado em http://%s:%s", Settings.HOST, Settings.PORT)
    app.run(host=Settings.HOST, port=Settings.PORT, debug=Settings.DEBUG)
