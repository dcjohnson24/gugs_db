from flask_login import UserMixin
from sqlalchemy.ext.hybrid import hybrid_property

from . import db


class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(100), unique=True)
    password = db.Column(db.String(100))
    name = db.Column(db.String(1000))


class Runner(db.Model):
    __tablename__ = 'runner'
    __table_args__ = (
        db.UniqueConstraint('firstname', 'secondname'),
    )

    id = db.Column(db.BigInteger, primary_key=True)
    firstname = db.Column(db.String)
    secondname = db.Column(db.String)
    gender = db.Column(db.String)
    age_cat_type_id = db.Column(db.Integer)

    # One to One relationship with RunnerContact
    runner_contact = db.relationship('RunnerContact',
                                     uselist=False,
                                     back_populates='runner')

    def __repr__(self):
        return '<Runner %r>' % self.id


class RunnerContact(db.Model):
    __tablename__ = 'runner_contact'

    id = db.Column(db.BigInteger, primary_key=True)
    runner_id = db.Column(db.BigInteger, db.ForeignKey('runner.id'))
    # One to One relationship with Runner
    runner = db.relationship('Runner', back_populates='runner_contact')
    # One to Many relationship with Race
    race = db.relationship('Race')

    title = db.Column(db.String)
    firstname = db.Column(db.String)
    secondname = db.Column(db.String)
    surname = db.Column(db.String)
    telephone_home = db.Column(db.String)
    cellphone = db.Column(db.String)
    fax = db.Column(db.String)
    email = db.Column(db.String)
    # TODO Find out how to set existing column as a primary key. Check uniqueness in pandas
    identification_code = db.Column(db.String)
    occupation = db.Column(db.String)
    telephone_work = db.Column(db.String)
    emergency1 = db.Column(db.String)
    emergencytel1 = db.Column(db.String)
    emergency2 = db.Column(db.String)
    emergencytel2 = db.Column(db.String)
    initials = db.Column(db.String)
    birthdate = db.Column(db.Date)
    created = db.Column(db.DateTime)
    nationality = db.Column(db.String)
    medical_aid = db.Column(db.Boolean)
    medical_aid_number = db.Column(db.String)
    disclaimer = db.Column(db.Boolean)
    medical_aid_name = db.Column(db.String)
    timingchip = db.Column(db.String)
    identificationtype = db.Column(db.String)
    language = db.Column(db.String)
    number = db.Column(db.String)
    year = db.Column(db.String)
    residential_address1 = db.Column(db.String)
    postal_address1 = db.Column(db.String)
    residential_address2 = db.Column(db.String)
    postal_address2 = db.Column(db.String)
    residential_address3 = db.Column(db.String)
    postal_address3 = db.Column(db.String)
    residential_province_id = db.Column(db.String)
    postal_province_id = db.Column(db.String)
    residential_city = db.Column(db.String)
    postal_city = db.Column(db.String)
    residential_suburb = db.Column(db.String)
    postal_suburb = db.Column(db.String)
    residential_postal_code = db.Column(db.String)
    postal_postal_code = db.Column(db.String)
    member_club_status = db.Column(db.String)
    club_name = db.Column(db.String)

    @hybrid_property
    def fullname(self):
        return f'{self.firstname} {self.secondname} {self.surname}'

    @fullname.expression
    def fullname(cls):
        return db.func.concat(cls.firstname, ' ', cls.secondname, ' ', cls.surname)


class Race(db.Model):
    __tablename__ = 'race'
    __table_args__ = (
        db.UniqueConstraint('name', 'race', 'time'),
    )

    id = db.Column(db.BigInteger, primary_key=True)
    # One to Many relationship with RunnerContact
    runner_contact_id = db.Column(
        db.BigInteger,
        db.ForeignKey('runner_contact.id')
    )
    pos = db.Column(db.Integer)
    name = db.Column(db.String)
    race = db.Column(db.String)
    time = db.Column(db.Interval)

    def __repr__(self):
        return '<Race %r>' % self.id


class RaceInfo:
    pass


class AgeCatType:
    pass
