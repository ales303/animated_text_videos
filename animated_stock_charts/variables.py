import mysql.connector
import pandas as pd
import datetime
import os
from dotenv import load_dotenv
from sqlalchemy import create_engine
from sql_credentials import sqlalchemy_credentials
from yfinance_data import blast_off


def log(msg):
    '''Simple logging with timestamp.'''
    print(f'\n{datetime.datetime.now()} {msg}')


def get_most_recent_close(symbol, days_back=0):
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


def get_stock_data_to_plot(symbol, only_get_most_recent_day=True, period_to_chart=None, use_yfinance_data=None):
    log("Getting stock data to plot")

    if period_to_chart == '1m' and use_yfinance_data:
        df = blast_off(stock_symbol=symbol, specific_date_to_process=None)  # '2023-10-20'
        df = df[["datetime", "open", "high", "low", "close"]]
        log("Retrieved stock data to plot from yfinance")

        df = create_new_stock_timeframe(df, output_mins_timeframe=2)

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

