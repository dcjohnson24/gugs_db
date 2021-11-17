import os

from dotenv import load_dotenv

load_dotenv()


class Config:
    user = os.getenv('POSTGRES_USER')
    password = os.getenv('POSTGRES_PASSWORD')
    load_data = int(os.getenv('LOAD_DATA', '0'))
    # if load_data:
    #     host = os.popen('docker-machine.exe ip').read().strip()
    # # You need this one when running with docker-compose locally
    # else:
    host = os.getenv('POSTGRES_HOST')
    database = os.getenv('POSTGRES_DB')
    port = os.getenv('POSTGRES_PORT')
    SQL_ALCHEMY_DATABASE_URI = f'postgresql+psycopg2://{user}:{password}@{host}:{port}/{database}'


class TestConfig(Config):
    TESTING = True
    DEBUG = True
    WTF_CSRF_ENABLED = False
    host = os.getenv('POSTGRES_HOST')
    # host = os.popen('docker-machine.exe ip').read().strip()
    port = 5433
    SQL_ALCHEMY_DATABASE_URI = f'postgresql+psycopg2://test_user:test_pass@{host}:{port}/gugs_test_db'


class ProductionConfig:
    # Heroku DATABASE_URL environment variable with throw an error claiming there is no dialect
    # called postgres
    # see 
    # https://stackoverflow.com/questions/35061914/how-to-change-database-url-for-a-heroku-application
    SQL_ALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL')
    if SQL_ALCHEMY_DATABASE_URI is None:
        pass
    elif SQL_ALCHEMY_DATABASE_URI.startswith('postgres://'):
        SQL_ALCHEMY_DATABASE_URI = SQL_ALCHEMY_DATABASE_URI.replace('postgres://', 'postgresql://', 1)
