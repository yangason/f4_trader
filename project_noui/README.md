# 增强版多窗口行情系统 - MySQL集成

这是一个基于HTML5和Flask的增强版多窗口行情系统，集成了MySQL数据库查询和策略数据展示功能。

## 功能特性

### 🎯 核心功能
- **多窗口K线图表**: 支持1x2、2x2、2x3等多种布局
- **MySQL数据库集成**: 直接从ASTOCK数据库查询股票数据
- **策略数据展示**: 显示策略的收益、回撤、交易记录等信息
- **技术指标**: 支持MA、RSI、MACD、布林带等技术指标
- **十字线同步**: 多窗口间的十字线位置同步
- **交易标记**: 在图表上显示买入/卖出标记

### 📊 数据源
- **K线数据**: 从MySQL的`zh_index`表查询
- **成交量数据**: 实时查询成交量和成交额
- **策略数据**: 通过API上传和展示策略结果
- **技术指标**: 实时计算和显示

## 系统架构

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   HTML前端      │    │   Flask API     │    │   MySQL数据库   │
│                 │◄──►│                 │◄──►│                 │
│ - 多窗口图表    │    │ - 数据查询接口  │    │ - zh_index表    │
│ - 策略面板      │    │ - 策略数据接口  │    │ - 股票数据      │
│ - 技术指标      │    │ - 指标计算      │    │ - 历史数据      │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

## 安装和配置

### 1. 环境要求
- Python 3.7+
- MySQL 5.7+
- 现代浏览器（Chrome、Firefox、Safari等）

### 2. 安装依赖
```bash
pip install flask flask-cors mysql-connector-python pandas numpy requests
```

### 3. 数据库配置
确保MySQL数据库`ASTOCK`已创建，并包含`zh_index`表：
```sql
CREATE DATABASE ASTOCK;
USE ASTOCK;

CREATE TABLE zh_index (
    id INT AUTO_INCREMENT PRIMARY KEY,
    symbol VARCHAR(20),
    exchange VARCHAR(10),
    datetime DATETIME,
    `interval` VARCHAR(10),
    volume DECIMAL(20,2),
    turnover DECIMAL(20,2),
    open_price DECIMAL(10,2),
    high_price DECIMAL(10,2),
    low_price DECIMAL(10,2),
    close_price DECIMAL(10,2),
    INDEX idx_symbol_datetime (symbol, datetime)
);
```

### 4. 修改数据库连接
在`api_server.py`中修改数据库连接参数：
```python
connection = mysql.connector.connect(
    host='localhost',
    port=3306,
    user='your_username',
    password='your_password',
    database='ASTOCK'
)
```

## 使用方法

### 1. 安装依赖
```bash
# 安装所有依赖（推荐）
python3 install.py

# 仅安装requirements.txt中的依赖
python3 install.py --requirements-only

# 仅安装子模块
python3 install.py --submodules-only

# 指定requirements.txt文件路径
python3 install.py --requirements path/to/requirements.txt
```

### 2. 启动系统
```bash
# 方法1: 使用完整启动脚本（推荐）
cd project_noui
chmod +x start_complete.sh
./start_complete.sh

# 方法2: 使用简化启动脚本
cd project_noui
chmod +x start_enhanced.sh
./start_enhanced.sh

# 方法3: 手动启动
cd project_noui
python3 api_server_simple.py &
open chart_enhanced.html  # macOS
# 或
xdg-open chart_enhanced.html  # Linux
# 或
start chart_enhanced.html  # Windows
```

### 2. 基本操作
1. **选择股票**: 在顶部下拉菜单中选择要查看的股票
2. **设置日期范围**: 选择开始和结束日期
3. **加载数据**: 点击"加载股票数据"按钮
4. **查看策略**: 点击"加载策略数据"按钮查看策略信息
5. **添加指标**: 在窗口中选择技术指标进行添加

### 3. 测试系统
```bash
cd project_noui
python3 test_system.py
```

### 4. 上传策略数据
```bash
cd project_noui
python3 upload_strategy_data.py
```

## API接口说明

### 股票数据接口
- `GET /api/stocks` - 获取所有可用股票列表
- `GET /api/bars` - 获取K线数据
- `GET /api/volume` - 获取成交量数据

### 策略数据接口
- `GET /api/trades` - 获取交易数据
- `GET /api/strategy_data` - 获取策略数据
- `POST /api/update_strategy_data` - 更新策略数据

### 技术指标接口
- `GET /api/indicators` - 获取技术指标数据

## 策略数据格式

### 技术数据格式
```python
tech_data = {
    'daily_df': pd.DataFrame({
        'net_pnl': [...],      # 日收益
        'drawdown': [...],     # 回撤
        'cumulative_pnl': [...] # 累计收益
    }, index=date_range)
}
```

### 交易数据格式
```python
trade_data = [
    {
        'time': timestamp,     # Unix时间戳
        'price': 100.0,        # 交易价格
        'volume': 1000,        # 交易量
        'direction': 'LONG',   # 方向：LONG/SHORT
        'offset': 'OPEN'       # 开平：OPEN/CLOSE
    }
]
```

## 文件结构

```
project_noui/
├── chart_enhanced.html      # 增强版HTML页面
├── api_server_simple.py    # 简化版Flask API服务器
├── api_server.py           # 完整版Flask API服务器
├── upload_strategy_data.py # 策略数据上传工具
├── test_system.py          # 系统测试脚本
├── start_complete.sh       # 完整启动脚本
├── start_enhanced.sh       # 简化启动脚本
├── requirements.txt        # Python依赖列表
├── README.md              # 说明文档
└── data/                  # 数据目录
    └── demo_data_1min.csv # 示例数据
```

```
jack_trader/
├── install.py             # 依赖安装脚本
├── project_noui/          # 项目目录
└── ...                    # 其他文件和目录
```

## 故障排除

### 常见问题

1. **API服务器无法启动**
   - 检查端口8800是否被占用
   - 确认Flask依赖已安装

2. **MySQL连接失败**
   - 检查MySQL服务是否运行
   - 确认数据库连接参数正确
   - 检查数据库和表是否存在

3. **数据加载失败**
   - 确认股票代码在数据库中存在
   - 检查日期范围是否有效
   - 查看浏览器控制台错误信息

4. **策略数据不显示**
   - 确认已上传策略数据
   - 检查数据格式是否正确
   - 查看API响应状态

### 调试模式
启动API服务器时添加调试信息：
```bash
FLASK_DEBUG=1 python3 api_server.py
```

## 扩展功能

### 添加新的技术指标
1. 在`api_server.py`的`get_indicators`函数中添加指标计算逻辑
2. 在前端HTML中添加指标选项
3. 更新指标颜色和标题配置

### 集成新的数据源
1. 修改`database_tools.py`中的查询函数
2. 更新API接口的数据格式
3. 调整前端的数据处理逻辑

### 自定义策略面板
1. 修改HTML中的策略面板样式
2. 添加新的策略数据字段
3. 更新策略数据的展示逻辑

## 许可证

本项目基于MIT许可证开源。

## 贡献

欢迎提交Issue和Pull Request来改进这个项目！

## 联系方式

如有问题或建议，请通过以下方式联系：
- 提交GitHub Issue
- 发送邮件至项目维护者 