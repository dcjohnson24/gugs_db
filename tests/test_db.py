from werkzeug.security import check_password_hash
from app.models import User


def test_new_user(new_user):
    assert new_user.email == 'some_user@gmail.com'
    assert check_password_hash(new_user.password, 'some_password')
    assert new_user.is_authenticated
    assert new_user.name == 'Some User'


def test_db(new_user, init_database):
    assert init_database.session.query(User).first().email == new_user.email
    assert (
        init_database.session.query(User).first().password == new_user.password
    )
