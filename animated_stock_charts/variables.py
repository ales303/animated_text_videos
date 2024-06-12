import mysql.connector
import pandas as pd
import datetime
import os
from dotenv import load_dotenv
from sqlalchemy import create_engine
from sql_credentials import sqlalchemy_credentials
from yfinance_data import blast_off
import sqlite3
from dotenv import load_dotenv
import time
import logging
import platform
import openai
from openai.error import RateLimitError, OpenAIError


def log(msg):
    '''Simple logging with timestamp.'''
    print(f'\n{datetime.datetime.now()} {msg}')


def get_most_recent_close(symbol, days_back=0):

    log("Starting to get most recent close")
    now = datetime.datetime.now()
    start_date = now - datetime.timedelta(days=10)
    start_date = start_date.strftime('%Y-%m-%d')
    df = blast_off(stock_symbol=symbol, specific_date_to_process=None, interval='1d', start_date=start_date)  # '2023-10-20'
    log("Retrieved stock daily close from yfinance")

    '''
    load_dotenv()

    log("Starting to get most recent close")
    table_suffix = 'daily'
    limit_size = 100

    db_connection = mysql.connector.connect(host=os.environ.get('ip'),
                                            user=os.environ.get('user'),
                                            passwd=os.environ.get('pwd'),
                                            database=os.environ.get('daily_db_name'))
    sql_query_fields = 'id, timestamp, symbol, date, open, high, low, close, volume'

    df = pd.read_sql(f'SELECT {sql_query_fields} FROM (SELECT * FROM `{symbol}_{table_suffix}` ORDER BY id DESC LIMIT {limit_size}) T1 ORDER BY id DESC', con=db_connection)

    log("Retrieved most recent close")
    return df['close'].iloc[days_back]
    '''

    return df['close'].iloc[-2]


def get_stock_data_to_plot(symbol, only_get_most_recent_day=True, period_to_chart=None, use_yfinance_data=None):
    log("Getting stock data to plot")

    if period_to_chart == '1m' and use_yfinance_data:
        df = blast_off(stock_symbol=symbol, specific_date_to_process=None)  # '2023-10-20'
        df = df[["datetime", "open", "high", "low", "close"]]
        log("Retrieved stock data to plot from yfinance")

        df = create_new_stock_timeframe(df, output_mins_timeframe=2)

        # Replace df index to reset the index timezone correctly
        df['datetime2'] = df['datetime'].astype('str')
        df['datetime2'] = df['datetime2'].str[:-6]
        df['datetime2'] = pd.to_datetime(df['datetime2'])
        df.set_index('datetime2', inplace=True)

        return df

    DB_CONNECTION_STRING = sqlalchemy_credentials(period_to_chart)
    engine = create_engine(DB_CONNECTION_STRING, pool_recycle=1)

    if period_to_chart == '1m':
        limit_size = 500
    elif period_to_chart == 'quarter':
        limit_size = 65
    elif period_to_chart == 'six_months':
        limit_size = 127
    elif period_to_chart == 'year':
        limit_size = 253

    table = f"{symbol}_1m_data" if period_to_chart == '1m' else f"{symbol}_daily"

    df = pd.read_sql(f'SELECT * FROM (SELECT * FROM `{table}` ORDER BY id DESC LIMIT {limit_size}) T1 ORDER BY id ASC', con=engine)

    if 'date' in df.columns:
        df['datetime'] = pd.to_datetime(df['date'])
    elif 'datetime' in df.columns:
        df['datetime'] = pd.to_datetime(df['datetime'])
    else:
        raise ValueError("The CSV must contain either a 'date' or 'datetime' column")

    df = df[["datetime", "open", "high", "low", "close"]]

    if only_get_most_recent_day:
        most_recent_day = df.datetime.iloc[-1].date()
        df = df[df.datetime.dt.date == most_recent_day]

    # Reduce the length of data for select period_to_chart by resampling their timeframe
    if period_to_chart == '1m':
        df = create_new_stock_timeframe(df, output_mins_timeframe=2)
    # elif period_to_chart == 'year':
    #     df = create_new_stock_timeframe(df, output_mins_timeframe=2, resample_daily_data=True)

    log("Retrieved stock data to plot from SQL database")
    return df


def create_new_stock_timeframe(input_dataframe, output_mins_timeframe=30, resample_daily_data=False):
    # Resampled data will be appended to the new dataframe.
    new_dataframe = pd.DataFrame(columns=input_dataframe.columns)

    # We need to set the index of the input dataframe to datetime in
    # order to resample it.
    datetime_index = pd.to_datetime(input_dataframe['datetime'])
    input_dataframe.set_index(datetime_index, inplace=True)

    # Convert the output_timeframe into string representation.
    if resample_daily_data:
        string_timeframe = '{}D'.format(output_mins_timeframe)
    else:
        string_timeframe = '{}min'.format(output_mins_timeframe)

    # The resample rule is a dictionary that specifies the aggregation method
    # used for different columns in the input dataframe.
    resample_rules = {
        'open': 'first',
        'high': max,
        'low': min,
        'close': 'last',
        # 'volume': sum  # Uncomment if your data has a volume column
    }

    # Check if we are resampling daily data or not
    if resample_daily_data:
        # Resample the entire dataframe without per-day grouping.
        resampled = input_dataframe.resample(rule=string_timeframe).apply(resample_rules)

        # Shift Saturdays and Sundays to the next Monday.
        resampled.index += pd.to_timedelta((resampled.index.weekday == 5) * 2, unit='D')  # Saturdays
        resampled.index += pd.to_timedelta((resampled.index.weekday == 6) * 1, unit='D')  # Sundays

        new_dataframe = new_dataframe.append(resampled)
    else:
        # Group the data by days and perform resampling to each day individually.
        # This will ensure that the results match the market hours.
        for date_index, date_group in input_dataframe.groupby(pd.Grouper(freq='D')):
            resampled = date_group.resample(
                rule=string_timeframe,
                origin='start').apply(resample_rules)
            new_dataframe = new_dataframe.append(resampled)

    # Set the new datetime column to the index of the new dataframe.
    new_dataframe['datetime'] = new_dataframe.index

    return new_dataframe


def create_animated_text_videos_db():
    # Connect to SQLite database (it will be created if it doesn't exist)
    conn = sqlite3.connect('/var/www/html/members.managed.capital/stock_videos/animated_text_videos.db') if platform.system() == "Linux" else sqlite3.connect('animated_text_videos.db')

    # Create a cursor object to execute SQL commands
    cursor = conn.cursor()

    # SQL command to create the videos table if it doesn't exist
    create_table_query = """
    CREATE TABLE IF NOT EXISTS videos (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        created_timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
        date DATE,
        symbol TEXT,
        filename TEXT,
        video_description TEXT DEFAULT NULL,
        uploaded_to_instagram_date DATETIME DEFAULT NULL,
        uploaded_to_tiktok_date DATETIME DEFAULT NULL
    );
    """

    # Execute the SQL command
    cursor.execute(create_table_query)

    # Commit the changes and close the connection
    conn.commit()
    conn.close()
    print("Database and table created successfully.")


def insert_video_record(date, symbol, filename, video_description):
    # Connect to SQLite database
    conn = sqlite3.connect('/var/www/html/members.managed.capital/stock_videos/animated_text_videos.db') if platform.system() == "Linux" else sqlite3.connect('animated_text_videos.db')

    # Create a cursor object to execute SQL commands
    cursor = conn.cursor()

    # SQL command to insert a new record into the videos table
    insert_query = """
    INSERT INTO videos (date, symbol, filename, video_description)
    VALUES (?, ?, ?, ?);
    """

    # Execute the SQL command with the provided parameters
    cursor.execute(insert_query, (date, symbol, filename, video_description))

    # Commit the changes and close the connection
    conn.commit()
    conn.close()
    print("Record inserted successfully.")


def get_openai_video_description(symbol, daily_change):
    # Load the .env file
    load_dotenv()
    openai.api_key = os.environ.get("openai_api_key")

    prompt = f"""
        Create a byline to publish with an Instagram or TikTok video for the stock symbol {symbol}, which today 
        performed {daily_change}%. Keep it to 1 sentence about the daily performance and 1 brief sentence that says to 
        watch a recap. Use a $ in the beginning of the symbol like ${symbol}. DO NOT use emojis. Only use common words. Do not 
        use the phrase 'Don't miss out'.
    """

    messages = [
        {"role": "system", "content": "You are making posts of videos on Instagram and \
        TikTok. The videos are the intraday trading action of stocks that people can watch to replay the day's action. \
        Each video shows the intraday action of just 1 stock."},
        {"role": "user", "content": prompt}
    ]

    max_retries = 5
    for retry in range(max_retries):
        try:
            print("Sending to API")
            response = openai.ChatCompletion.create(
                model="gpt-4",
                messages=messages,
                n=1,
                temperature=0.7
            )
            print("API response returned")
            print("Tokens used:", response['usage']['total_tokens'])
            return response.choices[0].message['content'].strip()

        except RateLimitError:
            wait_time = 2 ** retry  # Exponential backoff
            logging.warning(f"Rate limit exceeded. Retrying in {wait_time} seconds...")
            time.sleep(wait_time)
        except OpenAIError as e:
            logging.error(f"OpenAI API error: {e}")
            break
    return None

