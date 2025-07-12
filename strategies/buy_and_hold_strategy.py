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


class BuyAndHoldStrategy(TargetPosTemplate):
    """
    买入持有策略
    在策略启动时买入，然后长期持有不进行任何交易
    """

    author = "jack"

    # 策略参数
    hold_position: int = 1  # 持有仓位，1表示满仓持有，0表示不持有

    parameters = ["hold_position"]
    variables = ["bought"]

    def __init__(self, cta_engine, strategy_name: str, vt_symbol: str, setting: dict):
        """构造函数"""
        super().__init__(cta_engine, strategy_name, vt_symbol, setting)
        
        # 策略状态变量
        self.bought: bool = False  # 是否已经买入
        
        # 数据管理器
        self.bg = BarGenerator(self.on_bar)
        self.am = ArrayManager()

    def on_init(self) -> None:
        """
        策略初始化回调
        """
        self.write_log("买入持有策略初始化")
        
        # 加载历史数据
        self.load_bar(10)

    def on_start(self) -> None:
        """
        策略启动回调
        """
        self.write_log("买入持有策略启动")

    def on_stop(self) -> None:
        """
        策略停止回调
        """
        self.write_log("买入持有策略停止")

    def on_tick(self, tick: TickData) -> None:
        """
        收到tick数据推送
        """
        super().on_tick(tick)
        
        # 确保有tick数据后再执行买入
        if not self.bought and self.hold_position > 0:
            self.buy_and_hold()

    def on_bar(self, bar: BarData) -> None:
        """
        收到bar数据推送
        """
        super().on_bar(bar)
        
        # 更新技术指标数据
        self.am.update_bar(bar)
        
        # 确保有bar数据后再执行买入
        if not self.bought and self.hold_position > 0:
            self.buy_and_hold()

    def buy_and_hold(self) -> None:
        """
        执行买入持有操作
        """
        if self.bought:
            return
        
        # 检查是否有价格数据
        if not self.last_tick and not self.last_bar:
            self.write_log("等待价格数据...")
            return
            
        # 设置目标仓位
        self.set_target_pos(self.hold_position)
        self.bought = True
        
        self.write_log(f"执行买入持有操作，目标仓位：{self.hold_position}")

    def on_order(self, order: OrderData) -> None:
        """
        收到委托数据推送
        """
        super().on_order(order)
        
        # 记录订单信息
        self.write_log(f"委托更新：{order.vt_symbol} {order.direction.value} {order.offset.value} "
                      f"{order.volume}@{order.price} {order.status.value}")

    def on_trade(self, trade: TradeData) -> None:
        """
        收到成交数据推送
        """
        # 记录成交信息
        self.write_log(f"成交更新：{trade.vt_symbol} {trade.direction.value} {trade.offset.value} "
                      f"{trade.volume}@{trade.price}")
        
        # 更新界面
        self.put_event()

    def on_stop_order(self, stop_order: StopOrder) -> None:
        """
        收到停止单数据推送
        """
        self.write_log(f"停止单更新：{stop_order}")