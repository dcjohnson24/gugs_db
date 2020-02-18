from flask_table import Table, Col, DateCol


class RunnerResults(Table):
    id = Col('Id', show=False)
    title = Col('title')
    release_date = DateCol('release_date')
    
