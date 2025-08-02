#!/usr/bin/env python3
"""
创建测试策略数据，包含balance和drawdown曲线数据
"""

import requests
import json
import time
from datetime import datetime, timedelta
import random

def create_test_strategy_data():
    """创建测试策略数据"""
    
    base_url = "http://localhost:8800"
    
    print("📊 创建测试策略数据")
    print("=" * 50)
    
    # 生成测试数据
    start_date = datetime(2024, 1, 1)
    end_date = datetime(2024, 12, 31)
    current_date = start_date
    
    initial_balance = 1000000  # 初始资金100万
    current_balance = initial_balance
    peak_balance = initial_balance
    
    balance_data = []
    drawdown_data = []
    daily_pnl_data = []
    trades_data = []
    
    trade_id = 1
    
    print("1. 生成测试数据...")
    
    while current_date <= end_date:
        # 生成随机日收益率（-3% 到 +5%）
        daily_return = random.uniform(-0.03, 0.05)
        daily_pnl = current_balance * daily_return
        current_balance += daily_pnl
        
        # 更新峰值
        if current_balance > peak_balance:
            peak_balance = current_balance
        
        # 计算回撤
        drawdown_pct = (current_balance - peak_balance) / peak_balance * 100
        
        # 添加数据
        timestamp = int(current_date.timestamp())
        
        balance_data.append({
            'time': timestamp,
            'value': current_balance
        })
        
        drawdown_data.append({
            'time': timestamp,
            'value': drawdown_pct
        })
        
        daily_pnl_data.append({
            'time': timestamp,
            'value': daily_pnl
        })
        
        # 随机生成交易（30%概率）
        if random.random() < 0.3:
            direction = random.choice(['LONG', 'SHORT'])
            price = random.uniform(10, 100)
            volume = random.randint(100, 1000)
            
            trades_data.append({
                'id': trade_id,
                'time': timestamp,
                'direction': direction,
                'price': price,
                'volume': volume,
                'symbol': 'TEST_STOCK'
            })
            trade_id += 1
        
        # 下一天
        current_date += timedelta(days=1)
    
    print(f"   - 生成了 {len(balance_data)} 个Balance数据点")
    print(f"   - 生成了 {len(drawdown_data)} 个Drawdown数据点") 
    print(f"   - 生成了 {len(daily_pnl_data)} 个Daily PnL数据点")
    print(f"   - 生成了 {len(trades_data)} 笔交易")
    
    # 准备上传数据
    upload_data = {
        'symbol': 'test_strategy',
        'tech_data': {
            'daily_df': daily_pnl_data,
            'balance': balance_data,
            'drawdown': drawdown_data
        },
        'trade_data': trades_data
    }
    
    print("\n2. 上传测试数据到API服务器...")
    
    try:
        response = requests.post(
            f"{base_url}/api/update_strategy_data",
            json=upload_data,
            timeout=10
        )
        
        if response.status_code == 200:
            print("✅ 测试数据上传成功")
        else:
            print(f"❌ 数据上传失败: {response.status_code}")
            print(f"   响应: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ 数据上传异常: {e}")
        return False
    
    print("\n3. 验证数据上传...")
    
    try:
        # 验证策略数据
        response = requests.get(f"{base_url}/api/strategy_data?symbol=test_strategy")
        if response.status_code == 200:
            data = response.json()
            if 'strategy_data' in data:
                strategy_data = data['strategy_data']
                print("✅ 策略数据验证成功:")
                print(f"   - Balance数据: {len(strategy_data.get('balance', []))} 个数据点")
                print(f"   - Drawdown数据: {len(strategy_data.get('drawdown', []))} 个数据点")
                print(f"   - Daily PnL数据: {len(strategy_data.get('daily_pnl', []))} 个数据点")
            else:
                print("⚠️  没有找到策略数据")
        else:
            print(f"❌ 策略数据验证失败: {response.status_code}")
        
        # 验证交易数据
        response = requests.get(f"{base_url}/api/trades?symbol=test_strategy")
        if response.status_code == 200:
            data = response.json()
            if 'trades' in data:
                trades = data['trades']
                print(f"✅ 交易数据验证成功: {len(trades)} 笔交易")
            else:
                print("⚠️  没有找到交易数据")
        else:
            print(f"❌ 交易数据验证失败: {response.status_code}")
            
    except Exception as e:
        print(f"❌ 数据验证异常: {e}")
        return False
    
    print("\n✅ 测试数据创建完成！")
    print("\n🎯 使用方法:")
    print("1. 打开 chart_enhanced.html")
    print("2. 在标的选择器中选择 'test_strategy'")
    print("3. 点击'加载策略数据'按钮")
    print("4. 点击'策略面板'查看Balance和Drawdown曲线")
    
    return True

if __name__ == "__main__":
    create_test_strategy_data()