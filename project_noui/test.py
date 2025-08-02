import mysql.connector
import pandas as pd
from collections import defaultdict

def create_connection():
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
    
def get_min_market_value(year, month) -> list:
    # 获取市值数据
    market_values = get_market_values(year, month)

    # 按市值排序，选择前N个标的
    top_n = 10
    sorted_symbols = sorted(market_values, key=lambda x: x["market_value"])[:top_n]
    return sorted_symbols

def get_market_values(year, month) -> list:
    connection = create_connection()
    if not connection:
        return []
    
    finance_report_months = ['12', '03', '06', '09']
    year_of_interest = year - 1 if month < 4 else year
    report_month_of_interest = str(year_of_interest) + "-" + finance_report_months[(month - 1) // 3]

    cursor = connection.cursor()
    sql = f'''SELECT 
            a.symbol, a.name, a.update_time, (a.total_shares * b.close_price) AS market_value
            FROM finance a
            JOIN (
                SELECT 
                    symbol,
                    datetime,
                    close_price,
                    ROW_NUMBER() OVER (
                        PARTITION BY symbol, YEAR(datetime), MONTH(datetime) 
                        ORDER BY datetime DESC
                    ) as rn
                FROM daily
                WHERE exchange = 'SZSE'
                    AND datetime like '{report_month_of_interest}-%'
            ) b 
            ON a.symbol = b.symbol 
                AND YEAR(a.update_time) = YEAR(b.datetime)
                AND MONTH(a.update_time) = MONTH(b.datetime)
                AND b.rn = 1
            WHERE a.market = '深市'
                AND a.update_time like '{report_month_of_interest}-%'
                AND a.symbol like '00%'
                AND a.name not like '%ST%'
                AND a.name not like '%退'
            ;'''
    # print(f"SQL查询语句: {sql}")
    cursor.execute(sql)
    rows = cursor.fetchall()
    cursor.close()
    connection.close()

    # 将查询结果转换为字典列表
    values = [{"symbol": row[0], "name": row[1], "market_value": row[3]} for row in rows]
    return values

def convert_list_to_df(list_data)->pd.DataFrame:
    results = defaultdict(list)
    for data in list_data:
        for key, value in data.__dict__.items():
            results[key].append(value)
    df = pd.DataFrame.from_dict(results).set_index('datetime')
    return df

from vnpy.trader.optimize import OptimizationSetting
from vnpy_ctastrategy.backtesting import BacktestingEngine
from datetime import datetime
import sys
import os
import copy
from chart_tools import data

parent_dir = os.path.abspath(os.path.join(os.getcwd(), "."))
sys.path.append(parent_dir)
from strategies.monthly_min_market_value_strategy import MonthlyMinMarketValueStrategy

goods_symbols = []

# start_day = datetime(2024, 4, 1)
start_day = datetime(2025, 1, 1)
end_day = datetime(2025, 1, 31)

# 初始化列表
month_first_list = []
# current_date = start_day.replace(day=1)  # 确保从每月的1日开始
current_date = start_day

while current_date <= end_day:
    month_first_list.append(current_date)

    if current_date.month == 12:
        current_date = current_date.replace(year=current_date.year + 1, month=1, day=1)
    else:
        current_date = current_date.replace(month=current_date.month + 1, day=1)

# 输出结果
print(month_first_list)

capital = 1000000
total_profits = list()

record_df_dicts = list()
record_candle_dicts = list()
record_engines = list()
for i in range(len(month_first_list)):
    if i > 0:
        capital += total_profits[i - 1] / 10  # 累加上个月的总净利润
    record_df_dicts.append({})
    record_candle_dicts.append({})
    start = month_first_list[i]
    end = month_first_list[i + 1] if i + 1 < len(month_first_list) else end_day
    print(f"开始日期: {start}")
    
    min_market_symbols = get_min_market_value(start.year, start.month)

    # 按市值排序，选择前N个标的
    symbols_candidates = min_market_symbols[:2]
    month_profits = list() 
    month_profit = 0
    print(f"候选标的：{symbols_candidates}")
    for symbol in symbols_candidates:
        engine = BacktestingEngine()
        engine.set_parameters(
            vt_symbol=symbol["symbol"] + ".SZSE",
            interval="d",
            start=start,
            end=end,
            rate=0.3/10000,
            slippage=0.2,
            size=100,
            pricetick=0.2,
            capital=capital,
        )
        engine.add_strategy(MonthlyMinMarketValueStrategy, {"initial_capital": capital})

        engine.load_data()
        engine.run_backtesting()
        df = engine.calculate_result()
        
        record_df_dicts[i][symbol["symbol"]] = df
        record_candle_dicts[i][symbol["symbol"]] = engine.history_data
        res = engine.calculate_statistics()
        engine.cross_stop_order
        print(f"策略回测成功：{symbol['symbol']}，总净利润：{res['total_net_pnl']}")
        month_profits.append(res["total_net_pnl"])
        record_engines.append(copy.deepcopy(engine))
        
        data.update_tech_data(symbol["symbol"], 'result', df)
        data.update_bar_data(symbol["symbol"], convert_list_to_df(engine.history_data))
        data.update_volume_data(symbol["symbol"], convert_list_to_df(engine.history_data)[['volume']])
        if res["total_net_pnl"] > 0:
            goods_symbols.append({"symbol": symbol["symbol"], "total_net_pnl": res["total_net_pnl"]})
            # print(f"策略回测成功：{symbol}，总净利润：{res['total_net_pnl']}")
    month_profit = sum(month_profits)
    print(f"{start.year}-{start.month}月总净利润：{month_profit}")
    total_profits.append(month_profit)

print(f"总净利润：{sum(total_profits)}")


from chart_tools import app
app.run_server(debug=True, port=8880)