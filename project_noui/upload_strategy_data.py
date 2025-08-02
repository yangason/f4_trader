#!/usr/bin/env python3
"""
策略数据上传工具
演示如何将策略数据上传到API服务器
"""

import requests
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import json

# API服务器地址
API_BASE_URL = 'http://localhost:8800/api'

def create_sample_strategy_data(symbol, start_date, end_date):
    """
    创建示例策略数据
    """
    # 生成日期范围
    date_range = pd.date_range(start=start_date, end=end_date, freq='D')
    
    # 创建示例技术数据
    tech_data = {
        'daily_df': pd.DataFrame({
            'net_pnl': np.random.normal(1000, 500, len(date_range)),
            'drawdown': np.random.uniform(-5, 0, len(date_range)),
            'cumulative_pnl': np.cumsum(np.random.normal(1000, 500, len(date_range)))
        }, index=date_range)
    }
    
    # 创建示例交易数据
    trade_data = []
    for i in range(0, len(date_range), 5):  # 每5天一次交易
        if i < len(date_range):
            # 使用datetime对象的时间戳
            dt_obj = date_range[i]
            timestamp = int(dt_obj.timestamp())
            trade_data.append({
                'time': timestamp,
                'price': np.random.uniform(10, 100),
                'volume': np.random.randint(100, 1000),
                'direction': 'LONG' if np.random.random() > 0.5 else 'SHORT',
                'offset': 'OPEN' if np.random.random() > 0.5 else 'CLOSE'
            })
    
    return tech_data, trade_data

def upload_strategy_data(symbol, tech_data, trade_data):
    """
    上传策略数据到API服务器
    """
    try:
        url = f"{API_BASE_URL}/update_strategy_data"
        
        # 准备数据
        payload = {
            'symbol': symbol,
            'tech_data': {
                'daily_df': tech_data['daily_df'].to_dict('records') if 'daily_df' in tech_data else []
            },
            'trade_data': trade_data
        }
        
        # 发送请求
        response = requests.post(url, json=payload)
        
        if response.status_code == 200:
            print(f"✅ 成功上传 {symbol} 的策略数据")
            return True
        else:
            print(f"❌ 上传失败: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ 上传异常: {e}")
        return False

def get_available_stocks():
    """
    获取可用的股票列表
    """
    try:
        response = requests.get(f"{API_BASE_URL}/stocks")
        if response.status_code == 200:
            data = response.json()
            return data.get('stocks', [])
        else:
            print(f"❌ 获取股票列表失败: {response.text}")
            return []
    except Exception as e:
        print(f"❌ 获取股票列表异常: {e}")
        return []

def main():
    """
    主函数
    """
    print("🚀 策略数据上传工具")
    print("=" * 50)
    
    # 检查API服务器是否运行
    try:
        stocks = get_available_stocks()
        if not stocks:
            print("❌ 无法连接到API服务器或没有可用股票")
            print("请确保API服务器正在运行: python3 api_server.py")
            return
        
        print(f"✅ 找到 {len(stocks)} 只股票")
        
        # 选择股票
        print("\n可用的股票:")
        for i, stock in enumerate(stocks[:10]):  # 只显示前10只
            print(f"  {i+1}. {stock}")
        
        if len(stocks) > 10:
            print(f"  ... 还有 {len(stocks) - 10} 只股票")
        
        # 选择要上传数据的股票
        selected_stocks = stocks[:3]  # 为前3只股票创建示例数据
        
        # 设置日期范围
        end_date = datetime.now()
        start_date = end_date - timedelta(days=30)
        
        print(f"\n📅 数据日期范围: {start_date.strftime('%Y-%m-%d')} 到 {end_date.strftime('%Y-%m-%d')}")
        
        # 为每只股票创建并上传数据
        for symbol in selected_stocks:
            print(f"\n📊 为 {symbol} 创建示例策略数据...")
            
            tech_data, trade_data = create_sample_strategy_data(symbol, start_date, end_date)
            
            success = upload_strategy_data(symbol, tech_data, trade_data)
            
            if success:
                print(f"  - 技术数据: {len(tech_data['daily_df'])} 条记录")
                print(f"  - 交易数据: {len(trade_data)} 条记录")
        
        print("\n🎉 数据上传完成！")
        print("现在可以在HTML页面中点击'加载策略数据'按钮查看策略信息")
        
    except requests.exceptions.ConnectionError:
        print("❌ 无法连接到API服务器")
        print("请确保API服务器正在运行:")
        print("  python3 api_server.py (端口8800)")
    except Exception as e:
        print(f"❌ 发生错误: {e}")

if __name__ == "__main__":
    main() 