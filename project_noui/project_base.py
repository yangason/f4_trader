#!/usr/bin/env python3
"""
基础项目管理类
提供策略注册、运行和数据上传功能
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
import requests
import json

class ProjectBase:
    """基础项目管理类"""
    
    def __init__(self, name: str, api_url: str = "http://localhost:8800/api"):
        """
        初始化项目
        
        Args:
            name: 项目名称
            api_url: API服务器地址
        """
        self.name = name
        self.api_url = api_url
        self.trades = []  # 交易记录
        self.daily_pnl = []  # 日收益
        self.balance = []  # 账户余额
        self.drawdown = []  # 回撤
        self.start_time = None
        self.end_time = None
        self.initial_capital = 1000000
        self.current_capital = 1000000
        
    def register(self, register_dict: Dict[str, 'ProjectBase']):
        """
        向注册表中注册项目
        
        Args:
            register_dict: 注册表字典
        """
        register_dict[self.name] = self
        print(f"✅ 项目 {self.name} 已注册")
        
    def run(self, start_date: str, end_date: str, **kwargs):
        """
        运行项目（子类需要重写此方法）
        
        Args:
            start_date: 开始日期 (YYYY-MM-DD)
            end_date: 结束日期 (YYYY-MM-DD)
            **kwargs: 其他参数
        """
        self.start_time = datetime.strptime(start_date, '%Y-%m-%d')
        self.end_time = datetime.strptime(end_date, '%Y-%m-%d')
        print(f"🚀 开始运行项目 {self.name}")
        print(f"📅 时间范围: {start_date} 到 {end_date}")
        
        # 子类需要重写此方法实现具体策略
        raise NotImplementedError("子类必须重写run方法")
        
    def add_trade(self, symbol: str, direction: str, price: float, volume: float, 
                  timestamp: datetime, offset: str = "OPEN"):
        """
        添加交易记录
        
        Args:
            symbol: 股票代码
            direction: 方向 (LONG/SHORT)
            price: 价格
            volume: 数量
            timestamp: 时间戳
            offset: 开平 (OPEN/CLOSE)
        """
        trade = {
            'time': int(timestamp.timestamp()),
            'symbol': symbol,
            'direction': direction,
            'price': price,
            'volume': volume,
            'offset': offset
        }
        self.trades.append(trade)
        
    def add_daily_pnl(self, date: datetime, pnl: float):
        """
        添加日收益
        
        Args:
            date: 日期
            pnl: 收益
        """
        self.daily_pnl.append({
            'time': int(date.timestamp()),
            'value': pnl
        })
        
        # 更新账户余额
        self.current_capital += pnl
        self.balance.append({
            'time': int(date.timestamp()),
            'value': self.current_capital
        })
        
        # 计算回撤
        if self.balance:
            peak = max([b['value'] for b in self.balance])
            current_dd = (self.current_capital - peak) / peak * 100
            self.drawdown.append({
                'time': int(date.timestamp()),
                'value': current_dd
            })
            
    def upload_data(self):
        """
        上传数据到API服务器
        """
        try:
            # 准备上传数据
            upload_data = {
                'symbol': self.name,  # 使用项目名称作为symbol
                'tech_data': {
                    'daily_df': self.daily_pnl,
                    'balance': self.balance,
                    'drawdown': self.drawdown
                },
                'trade_data': self.trades
            }
            
            # 发送到API服务器
            response = requests.post(
                f"{self.api_url}/update_strategy_data",
                json=upload_data,
                timeout=10
            )
            
            if response.status_code == 200:
                print(f"✅ 项目 {self.name} 数据上传成功")
                return True
            else:
                print(f"❌ 数据上传失败: {response.status_code}")
                return False
                
        except Exception as e:
            print(f"❌ 数据上传异常: {e}")
            return False
            
    def get_summary(self) -> Dict[str, Any]:
        """
        获取项目摘要信息
        
        Returns:
            项目摘要字典
        """
        if not self.daily_pnl:
            return {
                'name': self.name,
                'status': '未运行',
                'trades_count': 0,
                'total_pnl': 0,
                'max_drawdown': 0
            }
            
        total_pnl = sum([d['value'] for d in self.daily_pnl])
        max_drawdown = min([d['value'] for d in self.drawdown]) if self.drawdown else 0
        
        return {
            'name': self.name,
            'status': '已完成',
            'start_time': self.start_time.isoformat() if self.start_time else None,
            'end_time': self.end_time.isoformat() if self.end_time else None,
            'trades_count': len(self.trades),
            'total_pnl': total_pnl,
            'max_drawdown': max_drawdown,
            'final_balance': self.current_capital
        }
        
    def print_summary(self):
        """打印项目摘要"""
        summary = self.get_summary()
        print(f"\n📊 项目 {self.name} 摘要:")
        print(f"   状态: {summary['status']}")
        print(f"   交易次数: {summary['trades_count']}")
        print(f"   总收益: {summary['total_pnl']:.2f}")
        print(f"   最大回撤: {summary['max_drawdown']:.2f}%")
        print(f"   最终余额: {summary['final_balance']:.2f}")


# 全局注册表
PROJECT_REGISTER = {}

def register_project(project: ProjectBase):
    """注册项目到全局注册表"""
    project.register(PROJECT_REGISTER)

def get_project(name: str) -> Optional[ProjectBase]:
    """从注册表获取项目"""
    return PROJECT_REGISTER.get(name)

def list_projects() -> List[str]:
    """列出所有注册的项目"""
    return list(PROJECT_REGISTER.keys())

def get_all_projects() -> Dict[str, ProjectBase]:
    """获取所有项目"""
    return PROJECT_REGISTER.copy()
