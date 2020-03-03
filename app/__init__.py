import os

from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_sslify import SSLify
from flask_migrate import Migrate

import config

db = SQLAlchemy()
migrate = Migrate()
login_manager = LoginManager()


def create_app():
    app = Flask(__name__)
    app.secret_key = os.urandom(24)
    env = os.getenv('FLASK_ENV', 'development')
    if env == 'production':
        SQL_ALCHEMY_DATABASE_URI = (
            config.ProductionConfig.SQL_ALCHEMY_DATABASE_URI
        )
    else:
        SQL_ALCHEMY_DATABASE_URI = config.Config.SQL_ALCHEMY_DATABASE_URI
    app.config['SQLALCHEMY_DATABASE_URI'] = SQL_ALCHEMY_DATABASE_URI
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    db.init_app(app)
    migrate.init_app(app, db)

    login_manager.login_view = 'auth.login'
    login_manager.init_app(app)

    if 'DYNO' in os.environ:
        SSLify(app)

    from .models import User

    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))

    from .routes import main as main_blueprint
    app.register_blueprint(main_blueprint)

    from .auth import auth as auth_blueprint
    app.register_blueprint(auth_blueprint)

    with app.app_context():
        from . import routes

        db.create_all()
        return app
