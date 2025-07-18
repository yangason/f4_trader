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

    def on_init(self) -> None:
        """
        策略初始化回调
        """
        self.write_log("每月市值最低策略初始化")
        self.load_bar(10)

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

    def on_bar(self, bar: BarData) -> None:
        """
        收到bar数据推送
        """
        super().on_bar(bar)

        if not self.buyed:
            capital = self.initial_capital
            size = self.get_size()
            target_pos = capital // (size * bar.close_price)
            print(f"当前资金: {capital}, 每个标的size: {size}, 目标仓位: {target_pos}")
            self.set_target_pos(target_pos)
            self.buyed = True
