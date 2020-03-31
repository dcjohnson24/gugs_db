import sys
import os
sys.path.append(os.pardir)

from typing import Callable
import pmdarima as pm
import datetime
import pandas as pd
import numpy as np
from sqlalchemy import create_engine
from fuzzywuzzy import process, fuzz
from tqdm import tqdm
# from sklearn.feature_extraction.text import TfidfVectorizer
# from sklearn.metrics.pairwise import cosine_similarity

from config import Config


def runner_groups(name: str, df: pd.DataFrame):
    runner_df = df.loc[df.name.str.contains(name, case=False)]
    return runner_df.groupby('distance_cat')


def predict_runner(name, df, n_forecasts=1):
    runner_df = df.loc[df.name.str.contains(name, case=False)]
    n_runners = runner_df.name.nunique()
    pred_list = []

    if n_runners == 1:
        pred_list.append(f'Results for {runner_df.name.unique()[0]}')
    elif n_runners > 1:
        matched_runners = runner_df.name.unique()
        names_str = (
            ', '.join(matched_runners[:-1]) + ', and ' + matched_runners[-1]
        )
        warning_string = (
            f'Runners {names_str} have been included in the prediction.'
            f' If this is incorrect, try using a full name search.'
        )
        pred_list.append(warning_string)

    groups = runner_df.groupby('distance_cat')

    for i, gp in groups:
        minutes = gp['time'].dropna().dt.seconds.values / 60.0
        len_minutes = len(minutes)
        if len_minutes > 1:
            try:
                model = pm.auto_arima(
                    minutes, start_p=0, start_q=0,
                    seasonal=False, suppress_warnings=True
                )
            except IndexError:
                # ARMA(p, q)
                model = pm.auto_arima(
                    minutes, start_p=0, d=0, start_q=0,
                    max_d=0, seasonal=False, suppress_warnings=True
                )
            actual_distances = gp['distance_km'].tolist()
            print(f'Category {i} km has {len_minutes}'
                  f' race(s) of distance '
                  f'{", ".join(map(str, actual_distances))} km')
            pred, conf_int = model.predict(n_forecasts, return_conf_int=True)

            def formatter(num):
                return str(datetime.timedelta(minutes=num)).split('.')[0]

            pred_format = formatter(pred[0])
            conf_int_format = [formatter(x) for x in conf_int[0]]
            pred_string = (f'The prediction for the next {i} km race'
                           f' is {pred_format} with 95 % confidence'
                           f' interval [{conf_int_format[0]},'
                           f' {conf_int_format[1]}]')
            print(pred_string)
            pred_list.append(pred_string)
        else:
            pred_string = (f'There was only {len_minutes} race(s) '
                           f'in category {i} km. Not enough for estimation')
            print(pred_string)
            pred_list.append(pred_string)
    return pred_list


if __name__ == '__main__':
    engine = create_engine(Config.SQL_ALCHEMY_DATABASE_URI)
    race_df = pd.read_sql_table('race', con=engine)

    for name in race_df.name.unique():
        print(f'Predictions for {name}')
        predict_runner(name, race_df)

    # Now do a value count of the problem races
    # There must be more than 2 races per runner for autoarima to work.
    groups = runner_groups('lizo', race_df)
