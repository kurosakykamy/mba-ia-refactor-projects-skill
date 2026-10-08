import logging

from flask import Flask
from flask_cors import CORS

from config.settings import Settings
from controllers.sistema_controller import health, index
from database import db
from middlewares.error_handler import register_error_handlers
from routes.report_routes import report_bp
from routes.task_routes import task_bp
from routes.user_routes import user_bp

logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s %(name)s %(message)s')
logger = logging.getLogger(__name__)


def create_app():
    app = Flask(__name__)
    app.config.from_object(Settings)

    CORS(app, origins=Settings.CORS_ORIGINS)
    db.init_app(app)

    app.register_blueprint(task_bp)
    app.register_blueprint(user_bp)
    app.register_blueprint(report_bp)

    app.add_url_rule('/health', view_func=health, methods=['GET'])
    app.add_url_rule('/', view_func=index, methods=['GET'])

    register_error_handlers(app)

    with app.app_context():
        db.create_all()

    return app


app = create_app()

if __name__ == '__main__':
    logger.info('Servidor iniciado em http://%s:%s', Settings.HOST, Settings.PORT)
    app.run(host=Settings.HOST, port=Settings.PORT, debug=Settings.DEBUG)
