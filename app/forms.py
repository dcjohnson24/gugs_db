from wtforms import Form, StringField, SelectField, IntegerField


class RunnerSearchForm(Form):
    choices = [('Runner Name', 'Runner Name')]
    select = SelectField('Search for GUGS runners:', choices=choices)
    search = StringField('Search by runner name')


class RunnerRaceSearchForm(Form):
    choices = [('Runner Name', 'Runner Name')]
    select = SelectField('Find races for a GUGS runner', choices=choices)
    search = StringField('Search by runner name')


class TopRunnerForm(Form):
    choices = [('male', 'Male'), ('female', 'Female')]
    select = SelectField('Find top runners by gender', choices=choices)
    search = StringField('Enter race name')
    n = IntegerField('Number of runners to display (integer)')
