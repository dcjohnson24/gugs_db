from flask import request, render_template, make_response, flash, redirect, url_for
from flask import current_app as app
from flask import Blueprint
from flask_login import login_required, current_user
from sqlalchemy.sql import func
from sqlalchemy import or_, and_
from datetime import datetime
import pandas as pd

from .models import db, RunnerContact, Race
from .forms import RunnerSearchForm, RunnerRaceSearchForm
import flask_table
from .tables import RunnerResults, RunnerRaceResults

main = Blueprint('main', __name__)


@main.route('/')
def index():
    return render_template('index.html')


@main.route('/profile')
@login_required
def profile():
    return render_template('profile.html', name=current_user.name)


@main.route('/search', methods=['GET', 'POST'])
@login_required
def search():
    search = RunnerSearchForm(request.form)
    if request.method == 'POST':
        return search_results(search)

    return render_template('search.html',
                           title="GUGS DB",
                           form=search,
                           name=current_user.name)


@main.route('/runner_race_search', methods=['GET', 'POST'])
def runner_race_search():
    search = RunnerRaceSearchForm(request.form)
    if request.method == 'POST':
        return search_runner_race_results(search)

    return render_template('search.html',
                           title="GUGS DB",
                           form=search)
                           # name=current_user.name)


@main.route('/results')
def search_results(search):
    results = []
    search_string = search.data['search']

    if search_string:
        if search.data['select'] == 'Runner Name':
            qry = RunnerContact.query.filter(
                func.similarity(RunnerContact.fullname, search_string) >= 0.3
            )
            results = qry.all()
        else:
            results = RunnerContact.query.all()
    else:
        results = RunnerContact.query.all()

    if not results:
        flash('No results found!')
        return redirect(url_for('main.search'))
    else:
        table = RunnerResults(results)
        table.border = True
        return render_template('results.html', table=table)


@main.route('/runner_race_results')
def search_runner_race_results(search):
    results = []
    search_string = search.data['search']

    if search_string:
        if search.data['select'] == 'Runner Name':
            # TODO make the similarity strength configurable
            # with the search term
            qry = Race.query.filter(
                func.similarity(Race.name, search_string) >= 0.3
            )
            results = qry.all()
        else:
            results = Race.query.all()
    else:
        results = Race.query.all()

    if not results:
        flash('No results found!')
        return redirect(url_for('main.runner_race_search'))
    else:
        table = RunnerRaceResults(results)
        table.border = True
        return render_template('results.html', table=table)