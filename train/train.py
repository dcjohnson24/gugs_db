import sys
import os
sys.path.append(os.pardir)

import warnings
import itertools
from typing import Callable
import pmdarima as pm
import datetime
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from sqlalchemy import create_engine
from fuzzywuzzy import process, fuzz
from tqdm import tqdm
# from sklearn.feature_extraction.text import TfidfVectorizer
# from sklearn.metrics.pairwise import cosine_similarity

from config import Config


def concat_names(df: pd.DataFrame, name_cols: list):
    df[name_cols] = df[name_cols].apply(lambda x: x.str.strip())
    df[name_cols] = df[name_cols].replace('NaN', '')
    df[name_cols] = df[name_cols].replace('none', '')
    df['name'] = df[name_cols].agg(' '.join, axis=1)
    df['name'] = df['name'].str.replace('  ', ' ')
    return df


def fuzzy_score_match(wrong_names: pd.Series,
                      correct_names: pd.Series,
                      scorer: Callable=fuzz.WRatio):
    assert isinstance(wrong_names, (pd.Series, np.array))
    assert isinstance(correct_names, (pd.Series, np.array))

    wrong_names = wrong_names.unique()
    correct_names = correct_names.unique()

    race_name_list = []
    similarity_list = []

    pbar = tqdm(wrong_names)
    for name in pbar:
        pbar.set_description(f'Find closest match for {name}')
        ratio = process.extract(name,
                                correct_names,
                                limit=1,
                                scorer=scorer)
        race_name_list.append(ratio[0][0])
        similarity_list.append(ratio[0][1])

    return pd.DataFrame({
        'actual_name': pd.Series(wrong_names),
        'matched_name': pd.Series(race_name_list),
        'similarity_score': pd.Series(similarity_list)
    })


def runner_groups(name: str, df: pd.DataFrame):
    runner_df = df.loc[df.name.str.contains(name, case=False)]
    return runner_df.groupby('distance_cat')


def predict_runner(name, df, n_forecasts=1):
    runner_df = df.loc[df.name.str.contains(name, case=False)]
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
            print(f'The prediction for the next {i} km race'
                  f' is \n {pred_format} with 95 % confidence'
                  f' interval {conf_int_format}')
        else:
            print(f'There was only {len_minutes} race(s) '
                  f'in category {i} km. Not enough for estimation')


if __name__ == '__main__':
    engine = create_engine(Config.SQL_ALCHEMY_DATABASE_URI)
    race_df = pd.read_sql_table('race', con=engine)

    for name in race_df.name.unique():
        print(f'Predictions for {name}')
        predict_runner(name, race_df))

    # Now do a value count of the problem races
    # There must be more than 2 races per runner for autoarima to work.
    groups = runner_groups('lizo', race_df)

   # TODO try with automated ARMA model filter.
   # Give up hyperparameter tuning and just make the endpoint.
    # res_list = []
    # for _, gp in groups:
    #     minutes = gp['time'].values / 60
    #     if len(minutes) > 1:
    #         res = arma_order_select_ic(minutes, ic='aic')
    #         res_list.append(res.aic_min_order)



    # for i, gp in race_df.groupby(['name', 'distance_cat']):
    #     seconds = gp['time'].dt.seconds.values
    #     seconds = np.reshape(seconds, (-1, 1))
    #     model = ARIMA(seconds, order=(0, 0, 0))
    #     model_fit = model.fit()
    #     print(model_fit.summary())

    # runner_df = pd.read_sql_table('runner_contact', con=engine)

    # name_cols = ['firstname', 'secondname', 'surname']
    # runner_df = concat_names(runner_df, name_cols=name_cols)

    # # race_df['distance_km'] = race_df['race'].apply(lambda x: x.split('_')[1].split('k')[0])
    # # race_df['distance_km'] = race_df['distance_km'].astype(float)

    # # TODO Compare these names against the race contact table
    # scorer_dict = {
    #     'R': fuzz.ratio,
    #     'PR': fuzz.partial_ratio,
    #     'TSeR': fuzz.token_set_ratio,
    #     'TSoR': fuzz.token_sort_ratio,
    #     'PTSeR': fuzz.partial_token_set_ratio,
    #     'PTSoR': fuzz.partial_token_sort_ratio,
    #     'WR': fuzz.WRatio,
    #     'QR': fuzz.QRatio,
    #     'UWR': fuzz.UWRatio,
    #     'UQR': fuzz.UQRatio
    # }

    # results_dict = {}
    # pbar = tqdm(scorer_dict)
    # for s in pbar:
    #     pbar.set_description(f'Matching using scorer {s}')
    #     results_df = fuzzy_score_match(wrong_names=race_df.name,
    #                                    correct_names=runner_df.name,
    #                                    scorer=scorer_dict[s])
    #     results_dict[s] = results_df

    # np.random.seed(846532)
    # n_runners = race_df.name.nunique()
    # idx = np.random.randint(n_runners, size=int(0.05*n_runners))
    # for score_func, df in results_dict.items():
    #     print(f'\nResults for {score_func}\n')
    #     print(df.iloc[idx])

    # TODO group duplicates based on string similarity
    # tfidf = TfidfVectorizer(analyzer='char')
    # names_list = race_df['name'].unique()
    # names_tfidf = tfidf.fit_transform(names_list)
    # cs_mat = cosine_similarity(names_tfidf)

    # # Find indices where > 0.8
    # matches = np.logical_and(cs_mat > 0.8, cs_mat < .99999)
    # idx = np.argsort(matches)

    # for i, x in enumerate(names_list):
    #     if matches[i].any():
    #         print(f"Similar names for {x}")
    #         print(names_list[matches[i]])

