import pandas as pd
import yfinance as yf
from datetime import datetime
from time import sleep, time


def log(msg):
    '''Simple logging with timestamp.'''
    print(f'\n{datetime.now()} {msg}')


def blast_off(stock_symbol, specific_date_to_process=None, interval="1m"):
    now = datetime.now()
    today = now.date().strftime('%Y-%m-%d')
    today = today if not specific_date_to_process else specific_date_to_process

    data = yf.download(f"{stock_symbol}", start=today, interval=interval)

    # Using rename can be tasking when renaming a large number of columns.
    # I have included an easier way below
    # data.rename(columns={'Open': 'open', 'Close': 'close', 'Low': 'low', 'High': 'high', 'Volume': 'volume', 'Datetime': 'datetime'}, inplace=True)

    # Because the function process is almost entierly iterative, utilize only one working dataframe if possible...
    # to is recommended optimize execution speed and memory use. But you can include another if its absolutely...
    # necessary or you wish to run a separate operation on the original

    # The reason why the 'symbol' column below was returning Nan values was because you had declared a new...
    # dataframe without a predefined set of values or indexes. I have corrected the order of which the columns should...
    # should have been set below. (Hint: Always start with the index because it is the reference point for each row)
    '''  
    df = pd.DataFrame()

    df['timestamp'] = data.index #####
    df['symbol'] = stock_symbol ######
    df['open'] = data['Open']
    df['high'] = data['High']
    df['low'] = data['Low']
    df['close'] = data['Close']
    df['volume'] = data['Volume']

    '''

    # As a point to note concerning stock data, its good practice to favor adj close over close price when available...
    # because it is the actual trading price in the exchanges after the stock splitting process.
    # In this case the values where the same for both but in some cases they usually are not e.g. Google and Amazon stock

    # you may always call in dataframe.columns to refer to their current names and mind the order of which they appear.
    print(data.columns)

    # Then assign the names you want in the order which they appear. (this is why it is important to mind their order.)
    data.columns = ['open', 'high', 'low', 'close', 'adj close', 'volume']

    # renaming the index is also as such. If you have more than one index, mid the order as well just like in the case...
    # of the columns
    data.index.names = ['timestamp']

    # Because the dataframe had a preset index when returned, it shall now be able to input the 'stock_symbol' due to...
    # a defined number of rows
    stock_symbol = stock_symbol.replace('-', '.')
    data['symbol'] = stock_symbol
    data['datetime'] = data.index
    # you may also rearange the order of which you wish to have them appear. Do not include the index name because it...
    # is not regarded as a column. Also, keep in mind the index is always on the left most handside, just like the..
    # row numbers in excel
    data = data[['datetime', 'symbol', 'open', 'high', 'low', 'close', 'adj close', 'volume']]

    data['close'] = data['close'].round(2)

    del data['adj close']

    data = data.drop_duplicates()

    # yfinance strangely gives a row of bad data for 16:00, this removes it
    data['datetime'] = pd.to_datetime(data['datetime'])
    data = data[data['datetime'].dt.hour < 16]

    print(data.tail(n=15))
    print('\n')
    # print(df.tail(n=30))

    return data


if __name__ == '__main__':
    symbols_to_loop = ['SPY']

    log('Starting now')

    for stock in symbols_to_loop:
        data = blast_off(stock_symbol=stock, specific_date_to_process='2023-10-20')

    log('Finished Now')

