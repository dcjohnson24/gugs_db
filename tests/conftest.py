import sys
import os
from os.path import dirname, abspath, join

# Weird hack to be able to import app module
# https://github.com/pytest-dev/pytest/issues/2421
path = abspath(join(dirname(__file__), os.pardir))
sys.path.insert(0, path)
import pytest
from sqlalchemy import exc
from werkzeug.security import generate_password_hash

from app.models import User
from app import create_app, db, login_manager


@pytest.fixture(scope='module')
def new_user():
    user = User(email='some_user@gmail.com',
                password=generate_password_hash('some_password', method='sha256'),
                name='Some User')
    return user


@pytest.fixture(scope='module')
def test_client():
    app = create_app()
    app.config.from_object('config.TestConfig')
    testing_client = app.test_client()
    ctx = app.app_context()
    ctx.push()

    yield testing_client

    ctx.pop()


@pytest.fixture(scope='module')
def init_database(test_client, new_user):
    db.create_all()

    if (db.session.query(User.email).filter_by(email='some_user@gmail.com')
            .scalar() is None):
        user1 = new_user
        db.session.add(user1)

    db.session.commit()

    yield db

    db.session.close()
    db.drop_all()
