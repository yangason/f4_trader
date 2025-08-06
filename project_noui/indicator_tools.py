#!/usr/bin/env python3
"""
技术指标工具
基于vnpy_ctastrategy的ArrayManager和BarData实现
"""

from typing import List, Dict, Any
import pandas as pd
import numpy as np
from datetime import datetime

# 导入vnpy相关模块
try:
    from vnpy_ctastrategy import ArrayManager
    from vnpy.trader.object import BarData
    from vnpy.trader.constant import Interval, Exchange
except ImportError as e:
    print(f"导入vnpy模块失败: {e}")
    print("请确保已安装vnpy_ctastrategy")

class IndicatorCalculator:
    """
    技术指标计算器
    基于ArrayManager实现各种技术指标
    """
    
    def __init__(self):
        """初始化指标计算器"""
        self.am = ArrayManager(100)  # 足够大的窗口来支持所有指标
        self.bars_data = []
        
    def add_bar(self, bar: BarData) -> None:
        """
        添加K线数据
        
        Args:
            bar: BarData对象
        """
        self.am.update_bar(bar)
        self.bars_data.append({
            'time': int(bar.datetime.timestamp()),
            'open': bar.open_price,
            'high': bar.high_price,
            'low': bar.low_price,
            'close': bar.close_price,
            'volume': bar.volume,
            'datetime': bar.datetime
        })
    
    def add_bars_from_dataframe(self, df: pd.DataFrame) -> None:
        """
        从DataFrame添加K线数据
        
        Args:
            df: 包含OHLCV数据的DataFrame
        """            
        for _, row in df.iterrows():
            # 创建BarData对象
            bar = BarData(
                symbol="",
                exchange=Exchange.LOCAL,  # 使用LOCAL交易所
                datetime=row['datetime'] if 'datetime' in row else pd.to_datetime(row['date']),
                interval=Interval.DAILY,
                volume=row['volume'],
                open_price=row['open'],
                high_price=row['high'],
                low_price=row['low'],
                close_price=row['close'],
                gateway_name=""
            )
            self.add_bar(bar)
    
    def get_ma_data(self, window: int) -> List[Dict[str, Any]]:
        """
        获取移动平均线数据
        
        Args:
            window: 移动平均窗口
            
        Returns:
            包含时间和MA值的列表
        """
        if not self.am.inited:
            return []
        
        ma_value = self.am.sma(window)
        
        return ma_value
    
    def get_rsi_data(self, window: int = 14) -> List[Dict[str, Any]]:
        """
        获取RSI数据
        
        Args:
            window: RSI计算窗口，默认14
            
        Returns:
            包含时间和RSI值的列表
        """
        if not self.am.inited:
            return []
        
        rsi_value = self.am.rsi(window)        
        return rsi_value
            
    def get_macd_data(self, fast_window: int = 12, slow_window: int = 26, signal_window: int = 9) -> Dict[str, List[Dict[str, Any]]]:
        """
        获取MACD数据
        
        Args:
            fast_window: 快线窗口，默认12
            slow_window: 慢线窗口，默认26
            signal_window: 信号线窗口，默认9
            
        Returns:
            包含MACD、信号线和柱状图的字典
        """
        if not self.am.inited:
            return {
                'macd': [],
                'signal': [],
                'histogram': []
            }
        
        macd_line, signal_line, histogram = self.am.macd(fast_window, slow_window, signal_window)
        
        result = {
            'macd': [],
            'signal': [],
            'histogram': []
        }
        
        result['macd'].append(macd_line)
        result['signal'].append(signal_line)
        result['histogram'].append(histogram)
        
        return result
    
    def _calculate_ema(self, data: np.ndarray, window: int) -> np.ndarray:
        """
        计算指数移动平均线
        
        Args:
            data: 价格数据
            window: 窗口大小
            
        Returns:
            EMA数组
        """
        alpha = 2.0 / (window + 1)
        ema = np.zeros_like(data)
        ema[0] = data[0]
        
        for i in range(1, len(data)):
            ema[i] = alpha * data[i] + (1 - alpha) * ema[i-1]
        
        return ema
        
    def clear_data(self) -> None:
        """清除所有数据"""
        self.am = ArrayManager(100)
        self.bars_data = []


def calculate_indicators_from_bars(bars_data: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    从K线数据计算技术指标
    
    Args:
        bars_data: K线数据列表，格式为[{'time': timestamp, 'open': float, 'high': float, 'low': float, 'close': float, 'volume': int}, ...]
        
    Returns:
        包含所有指标的字典
    """

    result = {
            'ma5': [],
            'ma10': [],
            'ma20': [],
            'ma60': [],
            'rsi': [],
            'macd': [],
            'signal': [],
            'histogram': []
        }
    calculator = IndicatorCalculator()
    
    # 将数据转换为BarData对象
    for i in range(len(bars_data)):
        bar_data = bars_data[i]
        bar = BarData(
            symbol="",
            exchange=Exchange.LOCAL,  # 使用LOCAL交易所
            datetime=datetime.fromtimestamp(bar_data['time']),
            interval=Interval.DAILY,
            volume=bar_data.get('volume', 0),
            open_price=bar_data['open'],
            high_price=bar_data['high'],
            low_price=bar_data['low'],
            close_price=bar_data['close'],
            gateway_name=""
        )
        calculator.add_bar(bar)

        if i >= 100:
            result['ma5'].append({
                'time': bar_data['time'],
                'value': calculator.get_ma_data(5)
            })
            result['ma10'].append({
                'time': bar_data['time'],
                'value': calculator.get_ma_data(10) 
            })
            result['ma20'].append({
                'time': bar_data['time'],
                'value': calculator.get_ma_data(20)
            })
            result['ma60'].append({
                'time': bar_data['time'],
                'value': calculator.get_ma_data(60)
            })
            result['rsi'].append({
                'time': bar_data['time'],
                'value': calculator.get_rsi_data(14)
            })

            macd_dict = calculator.get_macd_data()
            result['macd'].append({
                'time': bar_data['time'],
                'value': macd_dict['macd']
            })
            result['signal'].append({
                'time': bar_data['time'],
                'value': macd_dict['signal']
            })
            result['histogram'].append({
                'time': bar_data['time'],
                'value': macd_dict['histogram']
            })

    return result


# 示例使用
if __name__ == "__main__":
    # 创建示例数据
    sample_data = [
        {
            'time': 1640995200,  # 2022-01-01
            'open': 100.0,
            'high': 105.0,
            'low': 98.0,
            'close': 103.0,
            'volume': 1000
        },
        {
            'time': 1641081600,  # 2022-01-02
            'open': 103.0,
            'high': 108.0,
            'low': 102.0,
            'close': 106.0,
            'volume': 1200
        }
    ]
    
    # 计算指标
    indicators = calculate_indicators_from_bars(sample_data)
    
    print("技术指标计算结果:")
    print(f"MA5: {len(indicators['ma5'])} 条数据")
    print(f"MA10: {len(indicators['ma10'])} 条数据")
    print(f"MA20: {len(indicators['ma20'])} 条数据")
    print(f"MA60: {len(indicators['ma60'])} 条数据")
    print(f"RSI: {len(indicators['rsi'])} 条数据")
    print(f"MACD: {len(indicators['macd']['macd'])} 条数据") 