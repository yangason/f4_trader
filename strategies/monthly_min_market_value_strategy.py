from vnpy_ctastrategy import (
    StopOrder,
    TickData,
    BarData,
    TradeData,
    OrderData,
    BarGenerator,
    ArrayManager,
    TargetPosTemplate
)
from vnpy.trader.constant import Interval, Status

class MonthlyMinMarketValueStrategy(TargetPosTemplate):
    """
    每季度买入市值最低的10个标的，并在下个季度卖出。
    """

    author = "jack"

    initial_capital: int = 1000000  # 初始资金
    parameters = ["initial_capital"]
    

    # 策略参数
    def __init__(self, cta_engine, strategy_name: str, vt_symbol: str, setting: dict):
        """构造函数"""
        super().__init__(cta_engine, strategy_name, vt_symbol, setting)
        self.current_month = 0
        self.buyed = False
        self.season = 0
        self.bar_of_yesterday = None

    def on_init(self) -> None:
        """
        策略初始化回调
        """
        self.write_log("每月市值最低策略初始化")

        def set_yesterday_bar(bar):
            self.last_bar = bar
        self.load_bar(10, use_database=True, callback=set_yesterday_bar, interval=Interval.DAILY)
        self.bar_of_yesterday = self.last_bar
    
    def on_start(self) -> None:
        """
        策略启动回调
        """
        self.write_log("每月市值最低策略启动")

    def on_stop(self) -> None:
        """
        策略停止回调
        """
        self.write_log("每月市值最低策略停止")

    def on_order(self, order):
        if order.status == Status.ALLTRADED:
            print(f'订单状态更新: {order.status}, 价格: {order.price}, 数量: {order.volume}')
        return super().on_order(order)
    
    def on_trade(self, trade):
        return super().on_trade(trade)

    def on_bar(self, bar: BarData) -> None:
        """
        收到bar数据推送
        """
        super().on_bar(bar)
        can_buy = True
        if self.bar_of_yesterday.close_price * 1.09 <= bar.low_price and bar.low_price == bar.high_price:
            print(f'封板: {bar.symbol}, 日期: {bar.datetime}, 当前价格: {bar.close_price}')
            can_buy = False
        if not self.buyed and can_buy:
            capital = self.initial_capital
            size = self.get_size()
            target_pos = capital // (size * bar.close_price)
            print(f"日期: {bar.datetime}, 当前资金: {capital}, 交易单位: {size}, 目标仓位: {target_pos}, 目标价格: {bar.close_price}")
            self.set_target_pos(target_pos)
            self.buyed = True
        
        self.bar_of_yesterday = bar
        
