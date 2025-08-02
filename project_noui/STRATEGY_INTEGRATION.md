# 策略集成系统使用说明

## 概述

本系统提供了一个完整的策略管理框架，将 `monthly_min_market_value` 策略与 `chart_enhanced` 图表系统集成，实现策略运行、数据管理和可视化展示。

## 系统架构

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   ProjectBase   │    │   API Server    │    │   Chart System  │
│                 │◄──►│                 │◄──►│                 │
│ - 策略注册      │    │ - 数据接口      │    │ - 多窗口图表    │
│ - 策略运行      │    │ - 项目管理      │    │ - 策略数据展示  │
│ - 数据上传      │    │ - 数据存储      │    │ - 交易标记      │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

## 核心组件

### 1. ProjectBase 基础类 (`project_base.py`)

提供策略管理的基础功能：

- **初始化**: 设置项目名称、初始资金等参数
- **注册**: 向全局注册表注册项目
- **运行**: 执行策略逻辑
- **数据管理**: 记录交易、收益、回撤等数据
- **数据上传**: 将结果上传到API服务器

### 2. MonthlyMinMarketValueProject 策略类 (`monthly_min_market_value.py`)

基于 ProjectBase 重构的每月市值最低策略，**保持原有的vnpy engine框架**：

- **vnpy集成**: 使用vnpy的BacktestingEngine进行回测
- **策略框架**: 保持原有的MonthlyMinMarketValueStrategy策略逻辑
- **股票选择**: 每月选择市值最低的前N只股票
- **回测引擎**: 对每只股票单独运行vnpy回测引擎
- **数据管理**: 集成chart_tools的data对象进行数据管理
- **结果统计**: 计算综合统计结果和盈利股票分析

### 3. API服务器 (`api_server.py`)

提供数据接口和管理功能：

- **项目注册表**: 管理所有注册的策略项目
- **数据接口**: 提供股票数据、策略数据查询
- **项目管理**: 支持项目运行和状态查询
- **技术指标**: 计算MA、RSI等技术指标

## 使用方法

### 1. 启动系统

```bash
# 启动API服务器
python3 api_server.py

# 启动图表系统
open chart_enhanced.html
```

### 2. 创建和运行策略

```python
from project_base import register_project
from monthly_min_market_value import MonthlyMinMarketValueProject

# 创建策略实例
strategy = MonthlyMinMarketValueProject(
    name="monthly_min_market_value",
    initial_capital=1000000,
    top_n=10
)

# 注册策略
register_project(strategy)

# 运行策略（使用vnpy engine）
strategy.run(
    start_date="2024-01-01",
    end_date="2024-12-31"
)

# 获取详细摘要（包含vnpy特有统计）
strategy.print_detailed_summary()
```

### 3. 通过API运行策略

```bash
# 运行策略
curl -X POST http://localhost:8800/api/run_project \
  -H "Content-Type: application/json" \
  -d '{
    "project_name": "monthly_min_market_value",
    "start_date": "2024-01-01",
    "end_date": "2024-12-31"
  }'

# 获取项目摘要
curl http://localhost:8800/api/project/monthly_min_market_value

# 获取策略数据
curl http://localhost:8800/api/project/monthly_min_market_value/data
```

### 4. 在图表中查看策略数据

1. 打开 `chart_enhanced.html`
2. 选择项目名称作为股票代码
3. 点击"加载策略数据"查看策略结果
4. 使用"策略面板"查看详细统计信息

## API接口说明

### 项目管理接口

- `GET /api/projects` - 获取所有注册的项目
- `GET /api/project/<project_name>` - 获取项目摘要
- `GET /api/project/<project_name>/data` - 获取策略数据
- `POST /api/run_project` - 运行指定项目

### 数据查询接口

- `GET /api/stocks` - 获取股票列表
- `GET /api/bars` - 获取K线数据
- `GET /api/volume` - 获取成交量数据
- `GET /api/indicators` - 获取技术指标

### 数据上传接口

- `POST /api/update_strategy_data` - 上传策略数据

## 数据格式

### 策略数据格式

```python
{
    'daily_pnl': [
        {'time': timestamp, 'value': pnl_value},
        ...
    ],
    'drawdown': [
        {'time': timestamp, 'value': drawdown_percent},
        ...
    ],
    'balance': [
        {'time': timestamp, 'value': balance_value},
        ...
    ],
    'trades': [
        {
            'time': timestamp,
            'symbol': '000001',
            'direction': 'LONG',
            'price': 10.0,
            'volume': 1000,
            'offset': 'OPEN'
        },
        ...
    ]
}
```

### 项目摘要格式

```python
{
    'name': 'monthly_min_market_value',
    'status': '已完成',
    'start_time': '2024-01-01T00:00:00',
    'end_time': '2024-12-31T00:00:00',
    'trades_count': 120,
    'total_pnl': 150000.0,
    'max_drawdown': -5.2,
    'final_balance': 1150000.0
}
```

## 扩展开发

### 创建新的策略

#### 简单策略（直接实现）

1. 继承 `ProjectBase` 类
2. 重写 `run` 方法实现策略逻辑
3. 使用 `add_trade` 和 `add_daily_pnl` 记录数据
4. 注册到全局注册表

```python
class MyStrategy(ProjectBase):
    def __init__(self, name, **kwargs):
        super().__init__(name)
        # 初始化策略参数
        
    def run(self, start_date, end_date, **kwargs):
        super().run(start_date, end_date, **kwargs)
        # 实现策略逻辑
        # 记录交易和收益数据
        self.upload_data()

# 注册策略
strategy = MyStrategy("my_strategy")
register_project(strategy)
```

#### 基于vnpy的策略（保持原有框架）

1. 继承 `ProjectBase` 类
2. 在 `run` 方法中使用vnpy的BacktestingEngine
3. 保持原有的策略类实现
4. 集成chart_tools的data对象

```python
class MyVnpyStrategy(ProjectBase):
    def __init__(self, name, **kwargs):
        super().__init__(name)
        # 初始化策略参数
        
    def run(self, start_date, end_date, **kwargs):
        super().run(start_date, end_date, **kwargs)
        
        # 使用vnpy engine
        engine = BacktestingEngine()
        engine.set_parameters(...)
        engine.add_strategy(MyStrategyClass, {...})
        engine.load_data()
        engine.run_backtesting()
        
        # 处理结果并记录数据
        self.add_daily_pnl(date, pnl)
        self.upload_data()
```

### 添加新的API接口

在 `api_server.py` 中添加新的路由：

```python
@app.route('/api/my_endpoint', methods=['GET'])
def my_endpoint():
    # 实现接口逻辑
    return jsonify({'data': 'result'})
```

## 测试

运行测试脚本验证系统功能：

```bash
# 测试完整的策略集成系统
python3 test_strategy_integration.py

# 测试基于vnpy engine的重构策略
python3 test_vnpy_strategy.py
```

## 故障排除

### 常见问题

1. **API服务器无法启动**
   - 检查端口8800是否被占用
   - 确认依赖已正确安装

2. **策略运行失败**
   - 检查MySQL数据库连接
   - 确认数据表结构正确

3. **数据上传失败**
   - 检查API服务器是否运行
   - 确认网络连接正常

4. **图表无法显示数据**
   - 确认策略已运行并上传数据
   - 检查浏览器控制台错误信息

### 调试模式

启动API服务器时启用调试模式：

```bash
FLASK_DEBUG=1 python3 api_server.py
```

## 性能优化

1. **数据库优化**: 为常用查询添加索引
2. **缓存机制**: 缓存频繁查询的数据
3. **异步处理**: 使用异步任务处理长时间运行的策略
4. **数据分页**: 对大量数据进行分页处理

## 安全考虑

1. **数据验证**: 验证所有输入数据
2. **访问控制**: 限制API访问权限
3. **错误处理**: 妥善处理异常情况
4. **日志记录**: 记录重要操作日志 