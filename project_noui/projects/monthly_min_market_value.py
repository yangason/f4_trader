#!/usr/bin/env python3
"""
每月市值最低策略 - 基于ProjectBase重构
保持原有的vnpy engine框架实现
"""

import mysql.connector
import pandas as pd
from collections import defaultdict
from datetime import datetime
import sys
import os

# 添加项目根目录到路径
parent_dir = os.path.abspath(os.path.join(os.getcwd(), ".."))
sys.path.append(parent_dir)

from vnpy_ctastrategy.backtesting import BacktestingEngine
from strategies.monthly_min_market_value_strategy import MonthlyMinMarketValueStrategy
from tools.common import sum_specified_keep_others
from project_base import ProjectBase, register_project
from vnpy.trader.constant import Direction, Offset

class MonthlyMinMarketValueProject(ProjectBase):
    """每月市值最低策略项目"""
    
    def __init__(self, name: str = "monthly_min_market_value", 
                 initial_capital: float = 1000000,
                 top_n: int = 10):
        """
        初始化策略
        
        Args:
            name: 项目名称
            initial_capital: 初始资金
            top_n: 选择市值最低的前N只股票
        """
        super().__init__(name)
        self.initial_capital = initial_capital
        self.current_capital = initial_capital
        self.top_n = top_n
        
    def create_connection(self):
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
            
    def get_min_market_value(self, year: int, month: int) -> list:
        """获取指定年月市值最低的股票"""
        connection = self.create_connection()
        if not connection:
            return []
            
        try:
            finance_report_months = ['12', '03', '06', '09']
            year_of_interest = year - 1 if month < 4 else year
            report_month_of_interest = f"{year_of_interest}-{finance_report_months[(month - 1) // 3]}"
            
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
                    ORDER BY market_value ASC
                    LIMIT {self.top_n};'''
                    
            cursor.execute(sql)
            rows = cursor.fetchall()
            
            # 将查询结果转换为字典列表
            values = [{"symbol": row[0], "name": row[1], "market_value": row[3]} for row in rows]
            return values
            
        except Exception as e:
            print(f"获取市值数据失败: {e}")
            return []
        finally:
            connection.close()
            
    def convert_list_to_df(self, list_data) -> pd.DataFrame:
        df = pd.DataFrame()
        results = defaultdict(list)
        for data in list_data:
            for key, value in data.__dict__.items():
                results[key].append(value)
        if len(results) > 0:
            df = pd.DataFrame.from_dict(results).set_index('datetime')
        return df
        
    def run(self, start_date: str, end_date: str, **kwargs) -> pd.DataFrame:
        """
        运行策略
        
        Args:
            start_date: 开始日期 (YYYY-MM-DD)
            end_date: 结束日期 (YYYY-MM-DD)
            **kwargs: 其他参数
        """
        # 设置项目运行时间
        self.start_time = datetime.strptime(start_date, '%Y-%m-%d')
        self.end_time = datetime.strptime(end_date, '%Y-%m-%d')
        record_df = pd.DataFrame()
        print(f"🚀 开始运行项目 {self.name}")
        print(f"📅 时间范围: {start_date} 到 {end_date}")
        
        start_day = datetime.strptime(start_date, '%Y-%m-%d')
        end_day = datetime.strptime(end_date, '%Y-%m-%d')
        
        print(f"📊 开始运行每月市值最低策略")
        print(f"💰 初始资金: {self.initial_capital:,.2f}")
        print(f"🎯 选择股票数量: {self.top_n}")
        
        
        # 生成月份列表
        month_first_list = []
        total_profits = []
        current_date = start_day
        
        while current_date <= end_day:
            month_first_list.append(current_date)
            
            if current_date.month == 12:
                current_date = current_date.replace(year=current_date.year + 1, month=1, day=1)
            else:
                current_date = current_date.replace(month=current_date.month + 1, day=1)
        
        print(f"📅 月份列表: {month_first_list}")
        
        # 初始化变量
        capital = self.initial_capital / 10
        dfs = []
        
        # 按月份运行策略
        for i in range(len(month_first_list)):
            if i > 0:
                capital += total_profits[i - 1] / 10  # add profit
                            
            start = month_first_list[i]
            end = month_first_list[i + 1] if i + 1 < len(month_first_list) else end_day
            end = end.replace(month=end.month + 1, day=9) if end.month < 12 else end.replace(year=end.year+1, month=1, day=9)
            
            print(f"\n📅 处理 {start.year}-{start.month:02d}")
            
            # 获取当月市值最低的股票
            min_market_symbols = self.get_min_market_value(start.year, start.month)
            symbols_candidates = min_market_symbols[:]
            
            if not symbols_candidates:
                print(f"⚠️  {start.year}-{start.month:02d} 未找到符合条件的股票")
                total_profits.append(0)
                continue
                
            print(f"📈 候选标的: {symbols_candidates}")
            
            month_profits = []
            month_profit = 0
            
            # 对每只股票运行vnpy回测引擎
            for symbol in symbols_candidates:
                engine = BacktestingEngine()
                vt_symbol = symbol["symbol"] + ".SZSE"
                
                engine.set_parameters(
                    vt_symbol=vt_symbol,
                    interval="d",
                    start=start,
                    end=end,
                    rate=0.3/10000,
                    slippage=0.2,
                    size=100,
                    pricetick=0.2,
                    capital=capital,
                )
                engine.add_strategy(MonthlyMinMarketValueStrategy, {
                    "initial_capital": capital, 
                    "current_month": start.month
                })
                
                engine.load_data()
                engine.run_backtesting()
                df = engine.calculate_result()
                dfs.append(df)                
                res = engine.calculate_statistics(output=False)
                
                # 上传trade数据
                all_trades = engine.get_all_trades()
                print(f"📈 交易记录: {all_trades}")
                for trade in all_trades:
                    self.add_trade(
                        symbol=symbol['symbol'],
                        direction='LONG' if trade.direction == Direction.LONG else 'SHORT',
                        price=trade.price,
                        volume=trade.volume,
                        timestamp=trade.datetime,
                        offset='OPEN' if trade.offset == Offset.OPEN else 'CLOSE'
                    )
                
                month_profits.append(res["total_net_pnl"])                
            
            month_profit = sum(month_profits)
            total_profits.append(month_profit)
            print(f"📈 {start.year}-{start.month}月总净利润: {month_profit}")
        
        # 计算综合结果
        record_df = sum_specified_keep_others(
            dfs, 
            sum_columns=['trade_count', 'turnover', 'commission', 'slippage', 'trading_pnl', 'holding_pnl', 'total_pnl', 'net_pnl']
        )
        
        engine = BacktestingEngine()
        summary = engine.calculate_statistics(record_df, output=False, capital=self.initial_capital)
        
        print(f"\n🎉 策略运行完成")
        print(f"💰 总净利润: {sum(total_profits)}")
        print(f"📊 综合统计: {summary}")
                
        print(f"\n📤 上传数据到API服务器...")
        return record_df, summary


def main():
    """主函数"""
    # 创建策略实例
    strategy = MonthlyMinMarketValueProject(
        name="monthly_min_market_value",
        initial_capital=1000000,
        top_n=10
    )
    
    # 注册策略
    register_project(strategy)
    
    # 运行策略
    strategy.run(
        start_date="2024-01-01",
        end_date="2024-12-31"
    )
    


if __name__ == "__main__":
    main()