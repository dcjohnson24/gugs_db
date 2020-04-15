from flask_login import UserMixin
from sqlalchemy.ext.hybrid import hybrid_property

from . import db


class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(100), unique=True)
    password = db.Column(db.String(100))
    name = db.Column(db.String(1000))


class RunnerContact(db.Model):
    __tablename__ = 'runner_contact'
    __table_args__ = (
        db.UniqueConstraint('firstname', 'secondname',
                            'surname', 'identification_code'), )

    id = db.Column(db.BigInteger, primary_key=True)
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
        return db.func.concat(
            cls.firstname, ' ', cls.secondname, ' ', cls.surname
        )


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
    sex = db.Column(db.String)
    age = db.Column(db.Numeric)
    cat = db.Column(db.String)
    lic_no = db.Column(db.String)
    distance_km = db.Column(db.Float)
    race_year = db.Column(db.Integer)
    distance_cat = db.Column(db.String)

    def __repr__(self):
        return '<Race %r>' % self.id
