import requests
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import Select
from selenium.webdriver.support import expected_conditions as ec
from hidden_chrome_driver import HiddenChromeWebDriver
from pathlib import Path
import datetime
import calendar
import time
from tqdm import tqdm
import argparse


def select_month(browser, month: int=None):
    browser.find_elements(By.CLASS_NAME, 'spnMonthSelector')
    month_table = browser.find_element(By.ID, 'CalendarFilter')
    month_table.find_element(By.ID, str(month)).click()


def select_year(browser, year: int=None):
    select = Select(browser.find_element(By.ID, 'ddlSelectedYear'))
    select.select_by_visible_text(f'{year}')
    filter_btn = browser.find_element(By.CLASS_NAME, 'EventsFilterSubmit')
    filter_btn.send_keys('\n')


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


def parse_args():
    parser = argparse.ArgumentParser(description='Download WPA races')
    parser.add_argument('month',
                        type=int,
                        help='The month the race took place e.g. 1, 2, ...')
    parser.add_argument('year',
                        type=int,
                        help='The year the race took place')
    parser.add_argument('--download_path',
                        type=Path)

    args = parser.parse_args()
    return args


def main(month: int=None,
         year: int=None,
         download_path: Path=None,
         url: str="http://wpa.myactiveweb.co.za/calendar/dynamicevents.aspx",
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

    options = webdriver.ChromeOptions()

    if download_path:
        download_path = Path(download_path) / str(year) / month_abbr
        download_path.mkdir(exist_ok=True, parents=True)
        options = set_download_directory(path=download_path, options=options)
    else:
        download_path = Path.home() / 'Downloads'

    options.headless = True
    browser = HiddenChromeWebDriver(options=options, executable_path='/opt/chromedriver')
    browser.get(url)

    # Filter races by month
    print(f'Fetching {month_name} races for {year}\n')
    select_month(browser, month)
    # By default, the year in the dropdown list is the current year
    if year < current_year:
        select_year(browser, year)

    time.sleep(5)

    # Filter only road events
    select = Select(browser.find_element(By.ID, 'ddlTheme'))
    select.select_by_visible_text('Road')
    filter_btn = browser.find_element(By.CLASS_NAME, 'EventsFilterSubmit')
    filter_btn.send_keys('\n')

    time.sleep(5)

    excel_list = []
    div = browser.find_elements(By.TAG_NAME, 'a')
    for link in tqdm(div):
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
              f'{month_name} {current_year}\n')

    print(f'\nRace files saved to {download_path}')
    print(f'Finished in {datetime.timedelta(seconds=time.time()-start)}')
    browser.quit()


if __name__ == '__main__':
    args = parse_args()
    main(month=args.month, year=args.year, download_path=args.download_path)
