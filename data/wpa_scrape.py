# -*- coding: utf-8 -*-
"""
Spyder Editor

This is a temporary script file.
"""
import os

import requests
from selenium import webdriver
from selenium.webdriver.support.ui import Select
from selenium.webdriver.support import expected_conditions as ec
from data.hidden_chrome_driver import HiddenChromeWebDriver
from pathlib import Path
import datetime
import calendar
import time
# import gooey
import argparse


def select_month(browser, month: int=None):
    browser.find_elements_by_class_name('spnMonthSelector')
    month_table = browser.find_element_by_id('CalendarFilter')
    month_table.find_element_by_id(str(month)).click()


def select_year(browser, year: int=None):    
    select = Select(browser.find_element_by_id('ddlSelectedYear'))
    select.select_by_visible_text(f'{year}')
    browser.find_element_by_class_name('filterUpdate').click()


def set_download_directory(path: str, options: dict):
    if not isinstance(path, str):
        path = str(path)
    options.add_experimental_option("prefs", {
        "download.default_directory": path,
        "download.prompt_for_download": False,
        "download.directory_upgrade": True,
        "safebrowsing.enabled": True
    })
    return options


# @gooey.Gooey(program_name='Download WPA races')
# def parse_args_gooey():
#     parser = gooey.GooeyParser(description='Download WPA races')
#     parser.add_argument('month',
#                         type=int,
#                         help='The Month the race took place e.g. 1, 2, ...')
#     parser.add_argument('--download_path',
#                         action='store',
#                         widget='DirChooser',
#                         help='Directory to store downloaded races')
#     args = parser.parse_args()
#     return args

def parse_args():
    parser = argparse.ArgumentParser(description='Download WPA races')
    parser.add_argument('month',
                        type=int,
                        help='The Month the race took place e.g. 1, 2, ...')
    parser.add_argument('--download_path',
                        type=Path)
                        
    args = parser.parse_args()
    return args


def main(month: int=None,
         year: int=None,
         download_path: Path=None,
         max_attempts: int=5):
    current_month = datetime.datetime.now().month

    if month is None:
        month = current_month

    month_abbr = calendar.month_abbr[month]
    month_name = calendar.month_name[month]

    current_year = datetime.datetime.now().year
    if year is None:
        year = current_year

    if year > current_year:
        print(f"We aren't in {year} yet. Skipping...")
        return

    if month > current_month and year == current_year:
        print(f"We aren't in {month_name} {year} yet. Skipping...")
        return

    start = time.time()
    url = "http://www.wpa.org.za/calendar/dynamicevents.aspx"
    # You must check the box 'Use a proxy server' for proxy settings when connected to CPUT network
    # driver_path = Path.home() / 'gugs_db' / 'chromedriver'
    # driver_path = Path.home() / 'Documents' / 'RCS_GUGS_DB' / 'chromedriver.exe'

    options = webdriver.ChromeOptions()

    if download_path:
        download_path = Path(download_path) / month_abbr
        download_path.mkdir(exist_ok=True)
        options = set_download_directory(path=download_path, options=options)
    else:
        download_path = Path.home() / 'Downloads'

    options.headless = True
    browser = HiddenChromeWebDriver(options=options)
    # browser = HiddenChromeWebDriver(str(driver_path), options=options)
    browser.get(url)

    # Filter races by month
    print(f'Fetching {month_name} races for {year}\n')
    select_month(browser, month)
    # By default, the year in the dropdown list is the current year
    if year < current_year:
        select_year(browser, year)

    time.sleep(5)
    # Filter only road events

    select = Select(browser.find_element_by_id('ddlTheme'))
    select.select_by_visible_text('Road')
    browser.find_element_by_class_name('filterUpdate').click()

    time.sleep(5)

    excel_list = []
    div = browser.find_elements_by_tag_name('a')
    for link in div:
        for _ in range(max_attempts):
            try:
                item = link.get_attribute('href')
                break
            except ec.StaleElementReferenceException as e:
                print(e)
                time.sleep(2)
        if item:
            if any(item.endswith(ext) for ext in ['.xlsx', '.xls', '.csv']):
                item_name = item.split('/')[-1]
                print(f'Downloading {item_name}')
                excel_list.append(item)
                resp = requests.get(item)
                with open(download_path / item_name, 'wb') as output:
                    output.write(resp.content)
    if not excel_list:
        print(f'No road races found for '
              f'{month_name} {datetime.datetime.now().year}\n')

    print(f'\nRace files saved to {download_path}')
    print(f'Finished in {datetime.timedelta(seconds=time.time()-start)}')
    browser.quit()


if __name__ == '__main__':
    args = parse_args()
    main(month=args.month, download_path=args.download_path)
