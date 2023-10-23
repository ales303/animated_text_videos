import os
from dotenv import load_dotenv


def sqlalchemy_credentials(interval):
    # Load the .env file
    load_dotenv()

    database_prefix = os.environ.get('database_prefix')
    ip = os.environ.get('ip')
    pwd = os.environ.get('pwd')
    user = os.environ.get("user")

    if interval == '1m':
        database_name = f"{database_prefix}{interval}_stock_data"
        db_string = f'mysql+pymysql://{user}:{pwd}@{ip}/{database_name}'
    else:
        database_name = os.environ.get('daily_db_name')
        db_string = f'mysql+pymysql://{user}:{pwd}@{ip}/{database_name}'
        a = 'asdf'

    return db_string
