from flask import request, render_template, make_response, flash, redirect, url_for
from sqlalchemy.sql import func
from sqlalchemy import or_
from datetime import datetime
from flask import current_app as app
import pandas as pd

from .models import db, RunnerContact
from .forms import RunnerSearchForm
# from .tables import RunnerResults


@app.route('/', methods=['GET', 'POST'])
def home():
    search = RunnerSearchForm(request.form)
    if request.method == 'POST':
        return search_results(search)

    return render_template('search.html', title="GUGS DB", form=search)


@app.route('/results')
def search_results(search):
    results = []
    search_string = search.data['search']

    if search_string:
        if search.data['select'] == 'Runner Name':
            qry = RunnerContact.query.filter(
                or_(
                    RunnerContact.firstname.ilike('%'+search_string+'%'),
                    RunnerContact.secondname.ilike('%'+search_string+'%')
                )
            )   
            results = qry.all()
        # elif search.data['select'] == 'release year':
        #     qry = Runner.query.filter(func.extract('year', Runner.release_date) == search_string)
        #     results = qry.all()
        else:
            results = RunnerContact.query.all()
    else:
        results = RunnerContact.query.all()

    if not results:
        flash('No results found!')
        return redirect(url_for('home'))
    else:
        # table = RunnerResults(results)
        table = pd.read_sql(results.statement, con=db.engine)
        # table.border = True
        return render_template('results.html', table=table)
