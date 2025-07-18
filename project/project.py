import sys
import os
from datetime import datetime
from pathlib import Path
# 添加策略路径
PROJECT_ROOT = Path(__file__).parent.resolve()
os.chdir(PROJECT_ROOT)

from vnpy.event import EventEngine
from vnpy.trader.engine import MainEngine
from vnpy.trader.ui import MainWindow, create_qapp
from vnpy.trader.setting import SETTINGS

# 导入应用
from vnpy_ctastrategy import CtaStrategyApp
from vnpy_ctabacktester import CtaBacktesterApp
from vnpy_portfoliomanager import PortfolioManagerApp
from vnpy_datamanager import DataManagerApp
from vnpy_chartwizard import ChartWizardApp

# 导入策略
from strategies.buy_and_hold_strategy import BuyAndHoldStrategy


def main():
    """启动VeighNa UI界面"""
    # 配置设置
    # init_settings()
    
    # 创建QT应用
    qapp = create_qapp()
    
    # 创建事件引擎
    event_engine = EventEngine()
    
    # 创建主引擎
    main_engine = MainEngine(event_engine)

    # 强制重新设置工作目录
    os.chdir(PROJECT_ROOT)
    print(f"重新设置后工作目录: {Path.cwd()}")
    
    # 添加应用
    main_engine.add_app(CtaStrategyApp)
    main_engine.add_app(CtaBacktesterApp)
    main_engine.add_app(PortfolioManagerApp)
    main_engine.add_app(DataManagerApp)
    main_engine.add_app(ChartWizardApp)

    print(f"最终工作目录: {Path.cwd()}")

    # 创建主窗口
    main_window = MainWindow(main_engine, event_engine)
    main_window.showMaximized()
    
    print("VeighNa UI界面启动成功!")
    print("请在界面中打开'CTA回测'模块来运行买入持有策略")
    
    # 运行应用
    qapp.exec()

if __name__ == "__main__":
    main()