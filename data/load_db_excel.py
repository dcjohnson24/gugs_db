# -*- coding: utf-8 -*-

import pandas as pd
import numpy as np
from pathlib import Path
from typing import Dict
from sqlalchemy import create_engine
import io
import datetime

from data import wpa_scrape


REGEX = '^(Club|TeamName)'


def find_str(row, search_str: str) -> pd.Series:
    return row.astype(str).str.contains(search_str, case=False).any()


def find_header(df) -> int:
    s = df.apply(find_str, args=(REGEX,), axis=1)
    try:
        return df.loc[s].index.values[0] + 1
    except IndexError:
        s = df.columns.str.contains(REGEX, case=False)
        if pd.Series(s).sum() > 0:
            return 0
        else:
            return -99


def load_excel(xlsx: pd.ExcelFile, sheet_name: str = None) -> pd.DataFrame:
    if not sheet_name:
        sheet_name = xlsx.sheet_names[0]
    df = pd.read_excel(xlsx, sheet_name, nrows=20)
    start = find_header(df)
    if start == -99:
        # Edge case for Cape Peninsula marathon 21 km sheet with no column names
        new_df = pd.read_excel(xlsx, sheet_name)
        res = (
            (df.apply(lambda row: row.astype(str).str.contains('Cape Peninsula')
             .any(), axis=1)) &
            (df.apply(lambda row: row
             .astype(str).str.contains('21km').any(), axis=1))
        )
        if res.all():
            # Put the column headers as the first row and drop the first column
            # that is a duplicate of the index
            new_df = df.reset_index().T.reset_index().T.iloc[:, 1:]
            cols = [
                'Race', 'Event', 'Pos', 'FirstName', 'LastName',
                'Race No', 'Finish Status', 'Time', 'Age', 'Category',
                'Category Pos', 'Gender', 'Gender Pos', 'Club'
            ]
            new_df.columns = cols
    else:
        new_df = pd.read_excel(xlsx, sheet_name, header=start)
    return remove_footer(new_df)


def csv_to_xls(dir_list: list) -> None:
    count = 0
    for folder in dir_list:
        print(f'Searching folder {folder.stem} for .csv files')
        excel_files = [x for x in folder.iterdir() if x.is_file()]
        for xl in excel_files:
            if xl.suffix == '.csv':
                print(f'Found .csv file {xl.stem + xl.suffix}')
                df = pd.read_csv(xl)
                writer = pd.ExcelWriter(xl.with_suffix('.xlsx'))
                df.to_excel(writer, index=False)
                print(f'Removing .csv file {xl.stem + xl.suffix}')
                xl.unlink()
                count +=1
    print(f'\nThere were {count} .csv files converted')


def remove_footer(df: pd.DataFrame) -> pd.DataFrame:
    # Get all rows that have fewer than 8 missing values
    s = df.isnull().sum(axis=1) < df.shape[1] - 1
    return df.loc[s]


def find_race_sheets(xl: pd.ExcelFile) -> list:
    sheet_list = []
    for sheet in xl.sheet_names:
        df = pd.read_excel(xl, sheet_name=sheet)
        row_matches = df.apply(find_str, args=(REGEX,), axis=1).sum()
        column_matches = find_str(df.columns, REGEX)
        match_count = row_matches + column_matches
        try:
            if match_count > 0:
                new_df = load_excel(xl, sheet_name=sheet)
                if empty_col(new_df):
                    print(f"Time column is empty. Skipping sheet '{sheet}'")
                    continue
                else:
                    print(f"Saving sheet '{sheet}'")
                    sheet_list.append((sheet, new_df))
                
        except ValueError:
            if len(match_count) == 0:
                print(f'No matches for regex pattern {REGEX} found'
                      f" in sheet '{sheet}'")
            continue
    return sheet_list


def empty_col(df: pd.DataFrame) -> bool:
    time_cols = df.columns[df.columns.str.contains('TIME|FINISH', case=False)]
    print(f'Search for empty series in columns {time_cols}')
    return df[time_cols].isnull().all().any()


def col_finder(df: pd.DataFrame, search_str: str):
    return df.columns[df.columns.str.contains(search_str, case=False)]


def extract_race_sheets_excel(dir_list: list) -> Dict[str, pd.DataFrame]:
    sheets_dict = {}
    for folder in dir_list:
        print(f'Fetching excel workbooks for {folder.stem}')
        excel_files = [x for x in folder.iterdir() if x.is_file()]
        # Fetch sheet names of all excel books in directory
        xlsx_list = [pd.ExcelFile(excel_file) for excel_file in excel_files]
        for i, xl in enumerate(xlsx_list):
            print(f'\nSheets for workbook {excel_files[i].stem}')
            print('*' * 20)
            sheets_dict[f'{excel_files[i].stem}'] = find_race_sheets(xl)
    return sheets_dict


def load_to_db_table(df: pd.DataFrame,
                     engine,
                     table_name: str) -> None:
    df.head(0).to_sql(table_name,
                      engine,
                      if_exists='replace',
                      index=False) #truncates the table
    conn = engine.raw_connection()
    cur = conn.cursor()
    output = io.StringIO()
    df.to_csv(output, sep='\t', header=False, index=False)
    output.seek(0)
    contents = output.getvalue()
    cur.copy_from(output, table_name, null="") # null values become ''
    conn.commit()


def split_name_col(df: pd.DataFrame):
    df.columns = df.columns.str.upper()
    if not df.columns.str.match('SURNAME|LASTNAME|NAME 3').any():
        df[['FIRSTNAME', 'LASTNAME']] = df['NAME'].str.split(n=1, expand=True)
        df.drop(columns='NAME', inplace=True)
    elif df.columns.str.match('NAME 3').any():
        df['FIRSTNAME'] = df['NAME']
        df['LASTNAME'] = df['NAME 2'].str.cat(df['NAME 3'], na_rep='')
        #if df['NAME 3'].isna().all():
         #   df.drop(columns='NAME 3', inplace=True)
        df.drop(columns=['NAME', 'NAME 2', 'NAME 3'], inplace=True)
    return df


def concat_name_col(df: pd.DataFrame):
    df.columns = df.columns.str.upper()

    def concat_col(cols: list):
        if all(x in df.columns for x in cols):
            df['NAME'] = df[cols[0]].str.cat(df[cols[1:]], na_rep='', sep=' ')
            drop_cols = [x for x in cols if x != 'NAME']
            return df.drop(columns=drop_cols)

    name_combos = [
        ['NAME', 'SURNAME'], ['FIRSTNAME', 'LASTNAME'], ['NAME', 'NAME 2', 'NAME 3'],
        ['FIRST NAME', 'SURNAME', 'SURNAME 2', 'SURNAME 3'], ['FIRST NAME', 'LAST NAME']
    ]

    for combo in name_combos:
        s = concat_col(combo)
        if s is None:
            new_df = df
        else:
            new_df = s
    return new_df

    # df.columns = df.columns.str.upper()    
    # if all(x in df.columns for x in ['NAME', 'SURNAME']):
    #     df['NAME'] = df['NAME'].str.cat(df['SURNAME'], na_rep='', sep=' ')
    #     #df['NAME'] = df['NAME'] + ' ' + df['SURNAME']
    #     #if df['NAME'].isna().any():
    #     df.drop(columns='SURNAME', inplace=True)
    # elif all(x in df.columns for x in ['FIRSTNAME', 'LASTNAME']):
    #     df['NAME'] = df['FIRSTNAME'].str.cat(df['LASTNAME'], na_rep='', sep=' ')
    #     # df['NAME'] = df['FIRSTNAME'] + ' ' + df['LASTNAME']
    #     df.drop(columns=['FIRSTNAME', 'LASTNAME'], inplace=True)
    # elif all(x in df.columns for x in ['NAME', 'NAME 2', 'NAME 3']):
    #     df['NAME'] = df['NAME'].str.cat(df[['NAME 2', 'NAME 3']], na_rep='', sep=' ')
    #     df.drop(columns=['NAME 2', 'NAME 3'], inplace=True)
    # elif all(x in df.columns for x in ['FIRST NAME', 'SURNAME', 'SURNAME 2', 'SURNAME 3']):
    #     df['NAME'] = df['FIRST NAME'].str.cat(df[['SURNAME', 'SURNAME 2', 'SURNAME 3']], na_rep='', sep=' ')
    #     df.drop(columns=['FIRST NAME', 'SURNAME', 'SURNAME 2', 'SURNAME 3'], inplace=True)
    # return df


# Use explicit check for columns
def drop_cols(df: pd.DataFrame, cols_list: list) -> pd.DataFrame:
    idx = [x in df.columns for x in cols_list]
    drop_cols = [col for i, col in enumerate(cols_list) if idx[i]]
    return df.drop(columns=drop_cols)


def compile_gugs_data(sheets_dict: Dict[str, pd.DataFrame]):
    big_list = []
    race_cols = '|'.join(['TIME', 'FINISH', 'FINISH TIME', 'POS', 'Name',
                          'AGE', 'Participant', 'SEX', 'GENDER',
                          'LIC NO', 'LIC', 'CAT', 'LICENSE', 'LICENSENR',
                          'RACE NO', 'RACE NUMBER', 'RACENO', 'RACENUMBER',
                          'ELAPSED_TIME']) # 'BIB#', 'BIB'
    gugs_variants = '|'.join(['Gugs', 'RCS', 'Gugulethu'])
    replacements = {'TIME': ['FINISH',
                             'GUN FINISH',
                             'NETTIME',
                             'RACETIME',
                             'ELAPSED_TIME',
                             'FINISH TIME'],
                    'POS': ['POSITION'],
                    'LASTNAME': ['SURNAME', 'NAME 2', 'LAST NAME'],
                    'NAME': ['PARTICIPANT'],
                    'SEX': ['GENDER'],
                    'LIC NO': ['LICENSE', 'RACE NO',
                               'RACE NUMBER', 'RACENO',
                               'RACENUMBER', 'LICENSENR'],
                               #'BIB#', 'BIB'],
                    'CAT': ['CATEGORY']}
    #race_cols_full_set = set()
    race_cols_full_list = []
    club_col_set = set()
    for book, data_list in sheets_dict.items():
        if data_list:
            for sheet_name, data in data_list:
                race_table_cols = col_finder(data, race_cols)
                club_col = col_finder(data, REGEX)
                #race_cols_full_set.update(race_table_cols)
                race_cols_full_list.append(race_table_cols)
                club_col_set.update(club_col)
                try:
                    gugs = (data[data[club_col].squeeze()
                            .str.contains(gugs_variants, case=False, na=False)])
                except AttributeError as ae:
                    print(ae)
                    continue
                if gugs.empty:
                    print(f'No Gugs runners found for {book}'
                          f' on sheet {sheet_name}. Skipping')
                    continue
                race_table = gugs[race_table_cols]
                race_table['RACE'] = book + '_' + sheet_name
                # race_table = split_name_col(race_table)
                race_table = concat_name_col(race_table)
                race_table.columns = race_table.columns.str.upper()
                # race_table = drop_cols(
                #         race_table,
                #         cols_list=['CAT POS', 'GEN POS', 'TEAMNAME', 'MAT FINISH'])
                race_table.rename(
                        columns={el: k for k, v in replacements.items()
                                 for el in v},
                        inplace=True)
                big_list.append(race_table)
    # TODO Correct duplicate columns
    race_table_full = pd.concat(big_list,
                                axis=0,
                                ignore_index=True,
                                sort=True)
    return race_table_full, race_cols_full_list


def clean_time(df: pd.DataFrame) -> pd.DataFrame:
    df.time = df.time.astype(str)
    # Check for time stamps that have a period but not a semicolon
    gen_prob = df.loc[
            df.time
            .str.contains(r'(?=\.)(?!:)', na=False)]
    # Fixes for the WPARaceWalkingFiles that use H.M.S notation
    problems = gen_prob.loc[
            gen_prob.time.str.len() < 15
        ]
    mask = ((problems.time.str.split('.').str.len() > 2) &
            (problems.time.str.split('.').str[0].astype(int) > 20))
    problems.time[mask] = (
            '00:' + problems.time.str.split('.').str[:-1].str.join(':')
        )
    mask = problems.time.str.split('.').str.len() == 3
    problems.time[mask] = problems.time.str.replace('.', ':')

    problems.time = problems.time.str.replace('.', ':')

    mask = ((problems.time.str.split(':').str.len() == 2) &
            (problems.time.str.split(':').str[0].str.len() == 1))
    problems.time[mask] = '0' + problems.time[mask]
    mask = problems.time.str.split(':').str.len() == 2
    problems.time[mask] = '00:' + problems.time[mask]
    mask = problems.time.str.split(':').str[0] == '1'
    problems.time[mask] = '0'+problems.time[mask]

    gen_prob.time[problems.index] = problems.time

    # Remove milliseconds from string
    problem_15 = gen_prob.time.str.len() == 15
    gen_prob.time.loc[problem_15] = (
        gen_prob.time.loc[problem_15]
        .str.split('.').str[0]
    )
    problem_26 = gen_prob.time.str.len() == 26
    gen_prob.time.loc[problem_26] = (
            pd.to_datetime(
                    gen_prob.time.loc[problem_26])
                    .dt.time.astype(str).str.split('.').str[0]
        )
    df.time[gen_prob.index] = gen_prob.time
    df.time.replace('Not started', np.nan, inplace=True)
    mask = df.time.str.contains('1900', na=False)
    df.time[mask] = pd.to_datetime(df.time.astype(str)[mask]).dt.time

    df.time.replace('99:99:99', np.nan, inplace=True)
    df.time.replace('nan', np.nan, inplace=True)
    # Convert remainder to HH:MM:SS format
    mask = df.time.str.len() == 5
    df.time[mask] = '00:' + df.time[mask]
    mask = df.time.str.len() == 7
    df.time[mask] = '0' + df.time[mask]

    return df


def set_download_dir():
    return Path.home() / 'gugs_db' / 'data' / 'Race_downloads'


def scrape_all(download_path: str=None, year: int=None):
    if download_path is None:
        download_path = set_download_dir()

    for i in range(1, 13):
        wpa_scrape.main(month=i, download_path=download_path, year=year)


def append_results(download_path: str=None, year: int=None):
    # p = Path(r'C:\Users\dj3794\Documents\RCS_GUGS_DB\Race_downloads')
    if download_path is None:
        if year is None:
            year = datetime.datetime.now().year
        download_path = set_download_dir() / str(year)

    dir_list = [x for x in download_path.iterdir() if x.is_dir()]
    csv_to_xls(dir_list)

    sheets_dict = extract_race_sheets_excel(dir_list)
    race_table_full, cols_set = compile_gugs_data(sheets_dict)

    # Just leave the name as a single column in the DB
    race_table_full = (
        race_table_full.loc[:, ~race_table_full
                            .columns.str.contains('^Unnamed', case=False)]
    )
    race_table_full.columns = race_table_full.columns.str.lower()
    race_table_full = race_table_full[['pos', 'name',
                                       'race', 'time',
                                       'sex', 'age',
                                       'cat', 'lic no']]
    race_table_full.rename(columns={'lic no': 'lic_no'}, inplace=True)
    race_table_full_clean = clean_time(race_table_full)
    race_table_full_clean.time = pd.to_timedelta(
        race_table_full_clean.time.astype(str)
    )

    assert race_table_full_clean.name.notna().all()
    return race_table_full_clean


def main():
    engine = create_engine(
            'postgresql+psycopg2://postgres:gugulethu@localhost/gugs')
    scrape_all()
    race_table_full_clean = append_results()
    load_to_db_table(df=race_table_full_clean, engine=engine, table_name='race')


if __name__ == '__main__':
    # TODO change print statments to logging and save a log file
    # TODO Write function to break DataFrames to corresponding tables
    # Add the table to db and create primary key afterwards
    main()
