from . import db


class Runner(db.Model):
    __tablename__ = 'runner'
    #__table_args__ = {'extend_existing': True}

    id = db.Column(db.Integer, primary_key=True)
    firstname = db.Column(db.String)
    secondname = db.Column(db.String)
    gender = db.Column(db.String)
    age_cat_type_id = db.Column(db.Integer)

    runner_contact = db.relationship('RunnerContact',
                                     uselist=False,
                                     back_populates='runner')

    def __repr__(self):
        return '<Runner %r>' % self.id


class RunnerContact(db.Model):
    __tablename__ = 'runner_contact'
    #__table_args__ = {'extend_existing': True}

    id = db.Column(db.Integer, primary_key=True)
    runner_id = db.Column(db.Integer, db.ForeignKey('runner.id'))
    runner = db.relationship('Runner', back_populates='runner_contact')

    title = db.Column(db.Integer)
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
    created = db.Column(db.String)
    nationality = db.Column(db.String)
    medical_aid = db.Column(db.Boolean)
    medical_aid_number = db.Column(db.String)
    disclaimer = db.Column(db.Boolean)
    medical_aid_name = db.Column(db.String)
    timingchip = db.Column(db.String)
    identificationtype = db.Column(db.String)
    language = db.Column(db.String)
    number = db.Column(db.Integer)
    year = db.Column(db.Integer)
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

    runner = db.relationship('Runner', back_populates='runner_contact')


class Race:
    pass


class RaceInfo:
    pass


class AgeCatType:
    pass
