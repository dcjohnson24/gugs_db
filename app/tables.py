from flask_table import Table, Col, DateCol


class RunnerResults(Table):
    id = Col('Id', show=False)
    title = Col('title')
    runner_id = Col('runner_id')
    firstname = Col('firstname')
    secondname = Col('secondname')
    surname = Col('surname')
    telephone_home = Col('telephone_home')
    cellphone = Col('cellphone')
    fax = Col('fax')
    email = Col('email')
    # TODO Find out how to set existing column as a primary key. Check uniqueness in pandas
    identification_code = Col('identification_code')
    occupation = Col('occupation')
    telephone_work = Col('telephone_work')
    emergency1 = Col('emergency1')
    emergencytel1 = Col('emergencytel1')
    emergency2 = Col('emergency2')
    emergencytel2 = Col('emergencytel2')
    initials = Col('initials')
    birthdate = Col('birthdate')
    created = Col('created')
    nationality = Col('nationality')
    medical_aid = Col('medical_aid')
    medical_aid_number = Col('medical_aid_number')
    disclaimer = Col('disclaimer')
    medical_aid_name = Col('medical_aid_name')
    timingchip = Col('timingchip')
    identificationtype = Col('identificationtype')
    language = Col('language')
    number = Col('number')
    year = Col('year')
    residential_address1 = Col('residential_address1')
    postal_address1 = Col('postal_address1')
    residential_address2 = Col('residential_address2')
    postal_address2 = Col('postal_address2')
    residential_address3 = Col('residential_address3')
    postal_address3 = Col('postal_address3')
    residential_province_id = Col('residential_province_id')
    postal_province_id = Col('postal_province_id')
    residential_city = Col('residential_city')
    postal_city = Col('postal_city')
    residential_suburb = Col('residential_suburb')
    postal_suburb = Col('postal_suburb')
    residential_postal_code = Col('residential_postal_code')
    postal_postal_code = Col('postal_postal_code')
    member_club_status = Col('member_club_status')
    club_name = Col('club_name') 
