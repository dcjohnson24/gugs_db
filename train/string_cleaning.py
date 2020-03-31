import pandas as pd
import numpy as np
from typing import Callable
from fuzzywuzzy import process, fuzz
from tqdm import tqdm
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from sqlalchemy import create_engine

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


if __name__ == '__main__':
    engine = create_engine(Config.SQL_ALCHEMY_DATABASE_URI)

    runner_df = pd.read_sql_table('runner_contact', con=engine)
    race_df = pd.read_sql_table('race', con=engine)

    name_cols = ['firstname', 'secondname', 'surname']
    runner_df = concat_names(runner_df, name_cols=name_cols)

    # TODO Compare these names against the race contact table
    scorer_dict = {
        'R': fuzz.ratio,
        'PR': fuzz.partial_ratio,
        'TSeR': fuzz.token_set_ratio,
        'TSoR': fuzz.token_sort_ratio,
        'PTSeR': fuzz.partial_token_set_ratio,
        'PTSoR': fuzz.partial_token_sort_ratio,
        'WR': fuzz.WRatio,
        'QR': fuzz.QRatio,
        'UWR': fuzz.UWRatio,
        'UQR': fuzz.UQRatio
    }

    results_dict = {}
    pbar = tqdm(scorer_dict)
    for s in pbar:
        pbar.set_description(f'Matching using scorer {s}')
        results_df = fuzzy_score_match(wrong_names=race_df.name,
                                       correct_names=runner_df.name,
                                       scorer=scorer_dict[s])
        results_dict[s] = results_df

    np.random.seed(846532)
    n_runners = race_df.name.nunique()
    idx = np.random.randint(n_runners, size=int(0.05*n_runners))
    for score_func, df in results_dict.items():
        print(f'\nResults for {score_func}\n')
        print(df.iloc[idx])

    # TODO group duplicates based on string similarity
    tfidf = TfidfVectorizer(analyzer='char')
    names_list = race_df['name'].unique()
    names_tfidf = tfidf.fit_transform(names_list)
    cs_mat = cosine_similarity(names_tfidf)

    # Find indices where > 0.8
    matches = np.logical_and(cs_mat > 0.8, cs_mat < .99999)
    idx = np.argsort(matches)

    for i, x in enumerate(names_list):
        if matches[i].any():
            print(f"Similar names for {x}")
            print(names_list[matches[i]])
