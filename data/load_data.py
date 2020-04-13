import sys
import os
from pathlib import Path
sys.path.append(str(Path.home() / 'gugs_db' / 'data'))

import pandas as pd
import numpy as np
from sqlalchemy.sql import func, text
from sqlalchemy.exc import IntegrityError
from werkzeug.security import generate_password_hash
import datetime
from dotenv import load_dotenv
import argparse

from app import db, create_app
from app.models import RunnerContact, Runner, User, Race
from data.load_db_excel import scrape_all, append_results


def add_timestamp(timestamp):
    if timestamp != 0:
        return datetime.datetime(1601, 1, 1) + datetime.timedelta(seconds=timestamp/10000000)
    return np.nan


def clean_column_names(df):
    df.columns = df.columns.str.lower()
    df.columns = df.columns.str.replace(': ', '_')
    df = df.drop(df.columns[df.columns.str.contains('^unnamed')], axis=1)
    return df


def lower_string_df(df):
    return df.applymap(
        lambda s: " ".join(s.lower().split())
        if type(s) == str else s
    )


def create_id_col(df):
    return df.rename_axis('id').reset_index()


def reorder_cols(df):
    cols = df.columns.to_list()
    cols.remove('runner_id')
    cols = cols[:1] + ['runner_id'] + cols[1:]
    return df[cols]


def make_runnercontact_df(df: pd.DataFrame):
    df = clean_column_names(df)
    # Remove excess spaces in string
    df = lower_string_df(df)
    # Keep only GUGS runners
    df = df.loc[df['club_name'].str.contains('gugulethu')]

    # Drop duplicates
    dups_df = df.loc[df.duplicated(
        subset=['firstname', 'secondname', 'surname'], keep=False)
        | df.identification_code.duplicated(keep=False)]
    df = df.drop(dups_df.index)

    # Clean up nationality codes
    corrections = [
        ('germa', 'german'), ('malaw', 'malawian'), 
        ('rsa', 'south african'), ('south africa', 'south african'),
        ('zimba', 'zimbabwean'), ('america', 'united states'),
        ('0', 'south african')
    ]

    for prefix, cor in corrections:
        df.loc[df.nationality.str.contains(prefix), 'nationality'] = cor

    # Some nationality entries contain dates
    df.loc[df.nationality.apply(
           lambda s: any(str.isdigit(c) for c in s)), 'nationality'] = np.NaN
    df.rename(columns={'langauge': 'language'}, inplace=True)

    df.birthdate = pd.to_datetime(df.birthdate)
    df.fax = df.fax.astype(str)
    df.created = pd.to_datetime(df.created, format='%Y%m%d%H%M%S')
    df[['medical_aid', 'disclaimer']].astype(bool)
    num_cols = df._get_numeric_data().columns
    num_cols = [col for col in num_cols if col not in 
                ['medical_aid', 'disclaimer', 'number', 'year']]  
    df[num_cols] = df[num_cols].astype(str)
    return df


def fix_distances(problem_df: pd.DataFrame):
    # Mainly needed for 2019 data
    df = problem_df.copy(deep=True)

    def extract_and_replace(some_string: str):
        df.distance_km.loc[df.distance_km == some_string] = \
            df.race.loc[df.distance_km == some_string] \
            .str.extract(r'(\d{1,2}km)', expand=False)

    str_list = ['sheet1', 'results', 'wpa']
    for s in str_list:
        extract_and_replace(s)

    df.distance_km.loc[df.distance_km == '1o'] = '10'

    names = df.loc[df.distance_km == 'sheet2'].name.values
    if names.size > 0:
        def replace_wpa_walking(name: str, val: str):
            df.distance_km.loc[
                np.logical_and(df.name == name,
                               df.distance_km == 'sheet2')] = val

        rep_list = [
            (names[0], '10'), (names[1], '5'), (names[2], '3'),
            (names[3], '3'), (names[4], '3'), (names[5], '3'),
            (names[6], '1'), (names[7], '1')
        ]

        for name, val in rep_list:
            replace_wpa_walking(name, val)

    # Knysna forest
    df.distance_km.loc[
        np.logical_and(df.name == 'Bernard Rukadza',
                       df.distance_km == '')] = '42'
    df.distance_km.loc[df.distance_km == ''] = '21'

    def replace_missing_race(name, val):
        df.distance_km.loc[
            df.race == name
        ] = val

    repl_list = [
        ('avbobresults2019_wpa_fullresults', '15'),
        ('fnb122019fullresultsupdate_sheet1', '12'),
        ('satoricamelrunresults-05sep19_results', '16')
    ]

    for name, val in repl_list:
        replace_missing_race(name, val)

    df.distance_km = df.distance_km.str.split('.').str[0]
    df.distance_km = df.distance_km.str.split('km').str[0]

    df.distance_km = df.distance_km.astype(int)
    bins = [1, 5, 10, 21, 42, 50, 100]
    df['distance_cat'] = pd.cut(df.distance_km, bins, include_lowest=True)
    df.distance_cat = df.distance_cat.astype(str)
    return df


def create_race_table(scrape: bool=False, year: int=None):
    if scrape:
        scrape_all(year=year)
    df = append_results(year=year)
    df = lower_string_df(df)
    df.sex = df.sex.replace({'m': 'male'})
    df.sex = df.sex.replace({'f': 'female'})
    df = df.replace({pd.NaT: None})
    df['distance_km'] = df['race'].apply(lambda x: x.split('_')[1].split('k')[0])
    df['race_year'] = datetime.datetime.now().year if year is None else year
    df.lic_no = df.lic_no.fillna(np.nan)
    df['lic_no'] = df['lic_no'].astype(str).apply(lambda x: x.split('.')[0])
    mask = np.logical_and(
        df.lic_no.str.contains(r'[a-zA-Z]'),
        df.lic_no != 'nan')
    df.lic_no.loc[mask] = df.lic_no.loc[mask].str.split(r'[a-zA-Z]').str[-1]
    return df


def make_runner_df():
    runner_df = pd.DataFrame(
        {
            'firstname': ['Lizo', 'Xolani'],
            'secondname': ['Bango', 'B'],
            'gender': ['Male', 'Male'],
            'age_cat_type_id': [3, 2]
        }
    )
    runner_df = clean_column_names(runner_df)
    runner_df = lower_string_df(runner_df)
    return runner_df


def add_user(email: str, name: str, password: str):
    new_user = User(
        email=email,
        name=name,
        password=generate_password_hash(password, method='sha256')
    )
    # check whether user exists
    exists = db.session.query(User.email).filter_by(email=email).scalar() is not None
    if exists:
        return
    db.session.add(new_user)
    db.session.commit()


def load_df_orm(df, table):
    """Load table into SQL using ORM

    Arguments:
        df {pd.DataFrame} -- DataFrame matching the
            schema of the table class
        table {db.Model} -- the ORM model class
    """
    for _, row in df.iterrows():
        runner = table(**row.to_dict())
        try:
            db.session.add(runner)
            db.session.flush()
        except IntegrityError:
            db.session.rollback()
    db.session.commit()


def find_runner_races_contact(name: str,
                              similarity: float=0.3):
    # TODO Make query return the appropriate columns
    stmt = db.session.query(
        Race.pos, Race.name, Race.race, Race.time,
        RunnerContact.fullname, RunnerContact.birthdate
    ).select_from(Race).join(
        RunnerContact,
        func.similarity(Race.name, RunnerContact.fullname) > similarity
    ).subquery()
    return (
        db.session.query(stmt)
        .filter(func.similarity(stmt.c.name, name) > similarity).all()
    )


def find_runner_races(name: str,
                      similarity: float=0.3):
    # TODO Do a query on the race table alone
    # and compare the results with find_runner_races
    # It may make more sense to just be able to query races
    # for a person
    return db.session.query(Race).filter(
        func.similarity(Race.name, name) > similarity
    ).all()


def combine_race_years():
    race_df_list = []

    for year in [2019, 2020]:
        race_df = create_race_table(year=year)
        race_df = fix_distances(race_df)
        race_df_list.append(race_df)

    return race_df_list


if __name__ == '__main__':
    df = pd.read_csv('data/export.csv')
    clean_df = make_runnercontact_df(df)
    app = create_app()
    app.app_context().push()

    runner_df = make_runner_df()

    parser = argparse.ArgumentParser(description='Find races for a certain year')
    parser.add_argument('--year', type=int,
                        default=2020, help='Find races for a given year')
    # Calling --scrape will be True.
    parser.add_argument('--scrape', action='store_true')
    args = parser.parse_args()

    race_df = create_race_table(scrape=args.scrape, year=args.year)
    race_df = fix_distances(race_df)

    load_df_orm(race_df, Race)
    load_df_orm(runner_df, Runner)
    load_df_orm(clean_df, RunnerContact)
    add_user(email=os.getenv('ADMIN_EMAIL'),
             name=os.getenv('ADMIN_NAME'),
             password=os.getenv('ADMIN_PASSWORD'))
