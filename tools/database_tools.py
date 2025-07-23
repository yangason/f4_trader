from vnpy.trader.database import get_database
from vnpy.trader.object import BarData
from vnpy.trader.utility import extract_vt_symbol
from vnpy_mysql.mysql_database import MysqlDatabase, BarData
from datetime import datetime, date
from vnpy.trader.constant import  Direction, Exchange, Interval, Offset, Status, Product, OptionType, OrderType
from collections import defaultdict
import pandas as pd

def convert_list_to_df(list_data: list)->pd.DataFrame:
    results = defaultdict(list)
    for data in list_data:
        for key, value in data.__dict__.items():
            results[key].append(value)
    df = pd.DataFrame.from_dict(results).set_index('datetime')
    return df

def select_target_bars(vt_symbol, interval: Interval, start_date: date, end_date: date):
    symbol, exchange = extract_vt_symbol(vt_symbol=vt_symbol)
    database = get_database()
    results = database.load_bar_data(symbol=symbol, exchange=exchange, interval=interval, start=start_date, end=end_date)
    bars_df = convert_list_to_df(results)
    return bars_df
