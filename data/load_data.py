import sys
import os
from pathlib import Path
sys.path.append(Path.home() / 'gugs_db' / 'data')

import pandas as pd
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import IntegrityError
from werkzeug.security import generate_password_hash
import datetime

from app import db, create_app
from app.models import RunnerContact, Runner, User, Race
from data.load_db_excel import scrape_all, append_results


def ad_timestamp(timestamp):
    if timestamp != 0:
        return datetime.datetime(1601, 1, 1) + datetime.timedelta(seconds=timestamp/10000000)
    return pd.np.nan


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

    # Clean up nationality codes
    corrections = [
        ('germa', 'german'), ('malaw', 'malawian'), 
        ('rsa', 'south african'), ('south africa', 'south african'),
        ('zimba', 'zimbabwean'), ('america', 'united states'),
        ('0', 'south african')
    ]

    for prefix, cor in corrections:
        df.loc[df.nationality.str.contains(prefix), 'nationality'] = cor

    # Some nationality cells contain dates
    df.loc[df.nationality.apply(
           lambda s: any(str.isdigit(c) for c in s)), 'nationality'] = pd.np.NaN
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


def create_race_table(scrape: bool=False):
    if scrape:
        scrape_all()
    df = append_results()
    df = lower_string_df(df) 
    df = df.replace({pd.NaT: None})
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


if __name__ == '__main__':
    df = pd.read_csv('data/export.csv')
    clean_df = make_runnercontact_df(df)
    app = create_app()
    app.app_context().push()

    runner_df = make_runner_df()
    race_df = create_race_table()

    load_df_orm(runner_df, Runner)
    load_df_orm(clean_df, RunnerContact)
    load_df_orm(race_df, Race)

    add_user(email='drbangospeaks@gmail.com', name='Lizo', password='gugs2020')
