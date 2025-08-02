from vnpy.trader.database import get_database
from vnpy.trader.object import BarData
from vnpy.trader.utility import extract_vt_symbol
from vnpy_mysql.mysql_database import MysqlDatabase, BarData
from datetime import datetime, date
from vnpy.trader.constant import  Direction, Exchange, Interval, Offset, Status, Product, OptionType, OrderType
from collections import defaultdict
import pandas as pd

import sys
import os
parent_dir = os.path.abspath(os.path.join(os.path.curdir, "."))
sys.path.append(parent_dir)
from akshare.akshare.stock.stock_board_concept_em import stock_board_concept_hist_em
from akshare.akshare.index.index_stock_zh import stock_zh_index_daily_em

import mysql.connector

def create_connection():
    """创建MySQL连接"""
    try:
        connection = mysql.connector.connect(
            host='localhost',
            port=3306,
            user='root',
            password='123456',
            database='ASTOCK'  
        )
        return connection
    except mysql.connector.Error as e:
        print(f"连接MySQL失败: {e}")
        return None

def convert_list_to_df(list_data: list)->pd.DataFrame:
    results = defaultdict(list)
    for data in list_data:
        for key, value in data.__dict__.items():
            results[key].append(value)
    df = pd.DataFrame.from_dict(results).set_index('datetime')
    return df

def select_target_bars(vt_symbol, interval: Interval, start_date: datetime, end_date: datetime):
    symbol, exchange = extract_vt_symbol(vt_symbol=vt_symbol)
    database = get_database()
    results = database.load_bar_data(symbol=symbol, exchange=exchange, interval=interval, start=start_date, end=end_date)
    bars_df = convert_list_to_df(results)
    return bars_df

def insert_index_from_akshare(symbol: str, df: pd.DataFrame):

    field_mapping = {
        'date': 'datetime',
        '日期': 'datetime',
        'open': 'open_price',
        '开盘': 'open_price',
        'close': 'close_price',
        '收盘': 'close_price',
        'high': 'high_price',
        '最高': 'high_price',
        'low': 'low_price',
        '最低': 'low_price',
        '成交量': 'volume',
        '成交额': 'turnover',
        'amount': 'turnover'
    }

    connection = create_connection()
    # 数据清洗和转换
    for origin_column in df.columns:
        column = df[origin_column]
        if origin_column in field_mapping.keys():
            column = field_mapping[origin_column]
        df[column] = df[origin_column]
    
    df['symbol'] = symbol
    df['datetime'] = pd.to_datetime(df['datetime'])
    df['exchange'] = 'SSE' if (str(df['symbol'].iloc[0]).startswith('6') or str(df['symbol'].iloc[0]).startswith('sh')) else 'SZSE'
    df['interval'] = 'daily'
    
    # 选择需要的列
    columns_to_insert = ['symbol', 'exchange', 'datetime', 'interval', 
                        'volume', 'turnover', 'open_price', 
                        'high_price', 'low_price', 'close_price']
    df_clean = df[columns_to_insert]
    
    # 插入数据到MySQL
    cursor = connection.cursor()
    insert_query = """
    INSERT INTO zh_index (symbol, exchange, datetime, `interval`, volume, 
                                turnover, open_price, high_price, 
                                low_price, close_price)
    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
    """
    
    for index, row in df_clean.iterrows():
        cursor.execute(insert_query, tuple(row))
    
    connection.commit()
    cursor.close()

if __name__ == '__main__':
    start_date='20150101'
    end_date='20251231'
    small_concept_hist_em_df = stock_board_concept_hist_em('微盘股', period='daily', start_date=start_date, end_date=end_date, adjust='hfq')
    hs300_index_daily = stock_zh_index_daily_em('sz399300', start_date=start_date, end_date=end_date)
    insert_index_from_akshare('微盘股', small_concept_hist_em_df)
    insert_index_from_akshare('sz399300', hs300_index_daily)