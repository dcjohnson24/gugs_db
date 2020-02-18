import os

from flask import Flask, g
from flask_sqlalchemy import SQLAlchemy
from flask_session import Session

import config

db = SQLAlchemy()


def create_app():
    app = Flask(__name__)
    app.secret_key = os.urandom(24)
    env = os.getenv('FLASK_ENV', 'development')
    if env == 'production':
        SQL_ALCHEMY_DATABASE_URI = config.ProductionConfig.SQL_ALCHEMY_DATABASE_URI
    else:
        SQL_ALCHEMY_DATABASE_URI = config.Config.SQL_ALCHEMY_DATABASE_URI
    app.config['SQLALCHEMY_DATABASE_URI'] = SQL_ALCHEMY_DATABASE_URI
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    db.init_app(app)

    with app.app_context():
        from . import routes

        db.create_all()
        return app
