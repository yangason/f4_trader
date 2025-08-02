from vnpy_ctastrategy import (
    StopOrder,
    TickData,
    BarData,
    TradeData,
    OrderData,
    BarGenerator,
    ArrayManager,
    CtaSignal,
    TargetPosTemplate
)
from vnpy.trader.constant import Interval, Status

class RsiSignal(CtaSignal):
    """"""

    def __init__(self, rsi_window: int = 14, rsi_level: float = 20):
        super().__init__()

        self.rsi_window = rsi_window
        self.rsi_level = rsi_level
        self.rsi_long = 50 + self.rsi_level
        self.rsi_short = 50 - self.rsi_level

        self.bg = BarGenerator(self.on_bar)
        self.am = ArrayManager(20)

    def on_tick(self, tick: TickData) -> None:
        self.bg.update_tick(tick)

    def on_bar(self, bar: BarData) -> None:
        self.am.update_bar(bar)
        if not self.am.inited:
            self.set_signal_pos(0)

        rsi_value = self.am.rsi(self.rsi_window)

        if rsi_value >= self.rsi_long:
            self.set_signal_pos(1)
        elif rsi_value <= self.rsi_short:
            self.set_signal_pos(-1)
        else:
            self.set_signal_pos(0)

class MaCrossSignal(CtaSignal):

    def __init__(self, fast_window: int = 5, slow_window: int = 10):
        """"""
        super().__init__()

        self.fast_window = fast_window
        self.slow_window = slow_window

        self.bg = BarGenerator(self.on_bar)
        self.am = ArrayManager(20)

    def on_tick(self, tick: TickData) -> None:
        self.bg.update_tick(tick)

    def on_bar(self, bar: BarData) -> None:
        """
        Callback of new bar data update.
        """
        am = self.am
        am.update_bar(bar)
        if not am.inited:
            return

        fast_ma = am.sma(self.fast_window, array=True)
        self.fast_ma0 = fast_ma[-1]
        self.fast_ma1 = fast_ma[-2]

        slow_ma = am.sma(self.slow_window, array=True)
        self.slow_ma0 = slow_ma[-1]
        self.slow_ma1 = slow_ma[-2]        

        # cross
        cross_over = self.fast_ma0 > self.slow_ma0 and self.fast_ma1 < self.slow_ma1
        cross_below = self.fast_ma0 < self.slow_ma0 and self.fast_ma1 > self.slow_ma1

        if cross_over:
            self.set_signal_pos(1)
        elif cross_below:
            self.set_signal_pos(0)

class MonthlyMinMarketValueStrategy(TargetPosTemplate):
    """
    每季度买入市值最低的10个标的，并在下个季度卖出。
    """

    author = "jack"

    initial_capital: int = 1000000  # 初始资金
    current_month: int = 1
    parameters = ["initial_capital", "current_month"]
    

    # 策略参数
    def __init__(self, cta_engine, strategy_name: str, vt_symbol: str, setting: dict):
        """构造函数"""
        super().__init__(cta_engine, strategy_name, vt_symbol, setting)
        self.current_month = setting['current_month']
        self.buyed = False
        self.bar_of_yesterday = None
        self.rsi_signal = RsiSignal(14, 20)
        self.ma_cross_10_signal = MaCrossSignal(5, 10)
        self.ma_cross_20_signal = MaCrossSignal(5, 20)

    def on_init(self) -> None:
        """
        策略初始化回调
        """
        self.write_log("每月市值最低策略初始化")

        def call_back(bar):
            self.last_bar = bar
            self.rsi_signal.am.update_bar(bar)
            self.ma_cross_10_signal.am.update_bar(bar)
            self.ma_cross_20_signal.am.update_bar(bar)

        self.load_bar(20, use_database=True, callback=call_back, interval=Interval.DAILY)

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
        self.ma_cross_10_signal.on_bar(bar)
        self.ma_cross_20_signal.on_bar(bar)
        self.rsi_signal.on_bar(bar)

        can_buy = True
        if self.bar_of_yesterday.close_price * 1.09 <= bar.low_price and bar.low_price == bar.high_price:
            # print(f'封板: {bar.symbol}, 日期: {bar.datetime}, 当前价格: {bar.close_price}')
            can_buy = False
        if not self.buyed and can_buy and self.cal_signal() >= 1:
            capital = self.initial_capital
            size = self.get_size()
            target_pos = capital // (size * bar.close_price)
            self.set_target_pos(target_pos)
            print(f"symbol: {bar.symbol}, 日期: {bar.datetime}, 当前资金: {capital}, 交易单位: {size}, 目标仓位: {target_pos}, 目标价格: {bar.close_price}")
            self.buyed = True

        can_sell = True
        if self.bar_of_yesterday.close_price * 0.91 >= bar.low_price and bar.low_price == bar.high_price:
            # print(f'封板: {bar.symbol}, 日期: {bar.datetime}, 当前价格: {bar.close_price}')
            can_sell = False
        if self.buyed and can_sell and (bar.datetime.month > self.current_month or self.cal_signal() <= -1):
            target_pos = 0
            self.set_target_pos(0)
            print(f"symbol: {bar.symbol}, 日期: {bar.datetime}, 交易单位: {self.pos - target_pos}, 目标仓位: {target_pos}, 目标价格: {bar.close_price}")
            self.current_month = bar.datetime.month
        
        self.bar_of_yesterday = bar
        

    def cal_signal(self):
        
        ma_cross_10 = self.ma_cross_10_signal.get_signal_pos()
        ma_cross_20 = self.ma_cross_20_signal.get_signal_pos()

        ma_cross_signal_pos = ma_cross_10 or ma_cross_20
        rsi_signal_pos = self.rsi_signal.get_signal_pos()

        # print(f'ma_cross_signal_pos: {ma_cross_signal_pos}, ma_cross_10: {ma_cross_10}, ma_cross_20: {ma_cross_20}, rsi_signal_pos: {rsi_signal_pos}')
        return ma_cross_signal_pos + rsi_signal_pos