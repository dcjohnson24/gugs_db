from wtforms import Form, StringField, SelectField


class RunnerSearchForm(Form):
    choices = [('Runner Name', 'Runner Name')]
    select = SelectField('Search for GUGS runners:', choices=choices)
    search = StringField('')
