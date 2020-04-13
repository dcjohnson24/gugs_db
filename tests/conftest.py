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

from app.models import User, Race
from app import create_app, db, login_manager
from data.load_data import create_race_table, fix_distances, load_df_orm

@pytest.fixture(scope='module')
def new_user():
    user = User(email='some_user@gmail.com',
                password=generate_password_hash('some_password', method='sha256'),
                name='Some User')
    return user


@pytest.fixture(scope='module')
def race_data():
    race = Race(pos='200', name='Joe Smith', race='bellville', time='1:10:50',
                sex='male', age='41', cat='sen', lic_no='8023', distance_km='15',
                race_year='2020', distance_cat='(10.0, 21.0]')

    race1 = Race(pos='600', name='Joe Smith', race='capepeninsulamarathon',
                 time='03:42:43', sex='male', age='41', cat='sen',
                 lic_no='8023', distance_km='42', race_year='2020',
                 distance_cat='(21.0, 42.0]')

    race2 = Race(pos='110', name='Enzokuhle Khumalo', time='1:42:30',
                 sex='female', age='38', cat='sen', lic_no='3395',
                 distance_km='21', race_year='2020',
                 distance_cat='(10.0, 21.0]')

    race3 = Race(pos='720', name='Enzokuhle Khumalo', time='3:45:27',
                 sex='female', age='38', cat='sen', lic_no='3395',
                 distance_km='42', race_year='2020',
                 distance_cat='(21.0, 42.0]')
    race_df = create_race_table(year=2020)
    race_df = fix_distances(race_df)
    return [race, race1, race2, race3], race_df


@pytest.fixture(scope='module')
def app():
    app = create_app()
    app.config.from_object('config.TestConfig')
    app.app_context().push()
    return app


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
def init_database(test_client, new_user, race_data):
    db.create_all()
    with db.engine.connect() as con:
        con.execute('CREATE EXTENSION IF NOT EXISTS pg_trgm;')

    if (db.session.query(User.email).filter_by(email='some_user@gmail.com')
            .scalar() is None):
        # user1 = new_user
        db.session.add(new_user)

    race_data_list, race_df = race_data

    for r in race_data_list:
        db.session.add(r)

    load_df_orm(race_df, Race)

    db.session.commit()

    yield db

    db.session.close()
    db.drop_all()
