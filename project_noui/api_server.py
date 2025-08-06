from flask import Flask, request, jsonify
from flask_cors import CORS
import mysql.connector
import pandas as pd
from datetime import datetime, timedelta
import time
from typing import Union
import json
import os
import sys
from pathlib import Path
import importlib.util
import inspect

# 添加项目根目录到路径
parent_dir = os.path.abspath(os.path.join(os.getcwd(), ".."))
sys.path.append(parent_dir)

# 简化导入，避免akshare依赖问题
import mysql.connector
from datetime import datetime, timedelta
from vnpy.trader.constant import Interval

# 导入项目基础类
from project_base import PROJECT_REGISTER, get_project, list_projects, register_project, ProjectBase

# 导入技术指标工具
from indicator_tools import calculate_indicators_from_bars


app = Flask(__name__)
CORS(app)  # 允许跨域请求

# 全局数据对象，用于存储策略数据
class Data:
    def __init__(self):
        self.tech_data_dict = {}
        self.trade_data_dict = {}
        self.start_date = None
        self.end_date = None

data = Data()

def auto_register_projects(directory: str,
                      *,
                      base_class: type | None = ProjectBase,   # 限定必须继承某个基类；None 表示不限制
                      recursive: bool = True) -> None:
    """
    扫描目录 -> 动态导入模块 -> 找出类 -> 构造对象 -> 调用 register_project
    """
    if not directory:
        directory = os.path.join(os.path.dirname(__file__), "projects")
    
    dir_path = Path(directory).resolve()
    sys.path.insert(0, str(dir_path))

    pattern = "**/*.py" if recursive else "*.py"
    for file in dir_path.glob(pattern):
        if file.name.startswith("_"):
            continue

        module_name = f"_auto_{file.stem}_{file.stat().st_ino}"
        spec = importlib.util.spec_from_file_location(module_name, file)
        if spec is None:
            continue
        module = importlib.util.module_from_spec(spec)
        sys.modules[module_name] = module

        try:
            assert isinstance(spec.loader, importlib.abc.Loader)
            spec.loader.exec_module(module)
        except Exception as e:
            print(f"[WARN] 加载 {file} 失败: {e}")
            continue

        for _, cls in inspect.getmembers(module, inspect.isclass):
            if cls.__module__ != module.__name__:
                continue
            if base_class is not None and not issubclass(cls, base_class):
                print(f"[WARN] {cls} 不是 {base_class} 的子类, 跳过")
                continue
            try:
                obj = cls()
            except TypeError as e:
                print(f"[WARN] 实例化 {cls} 失败: {e}")
                continue

            try:
                register_project(obj)
            except Exception as e:
                print(f"[WARN] register_project 调用失败: {e}")

def select_target_bars_direct(symbol, start_date, end_date):
    """直接查询数据库获取K线数据"""
    try:
        connection = create_mysql_connection()
        if not connection:
            return None

        table = None
        if symbol.startswith('000') or symbol.startswith('399') or symbol.startswith('688') or symbol.startswith('60'):
            table = 'daily_hfq'            
        else:
            table = 'zh_index'
        
        cursor = connection.cursor()
        query = f"""
        SELECT datetime, open_price, high_price, low_price, close_price, volume, turnover
        FROM `{table}` 
        WHERE symbol = %s AND datetime >= %s AND datetime < %s 
        ORDER BY datetime
        """
        cursor.execute(query, (symbol, start_date, end_date))
        
        results = cursor.fetchall()
        cursor.close()
        connection.close()
        
        if not results:
            return None
        
        # 转换为DataFrame
        df = pd.DataFrame(results, columns=['datetime', 'open_price', 'high_price', 'low_price', 'close_price', 'volume', 'turnover'])
        df.set_index('datetime', inplace=True)
        
        return df
    except Exception as e:
        print(f"查询数据失败: {e}")
        return None

def create_mysql_connection():
    """创建MySQL连接"""
    try:
        connection = mysql.connector.connect(
            host='localhost',
            port=3306,
            user='root',
            password='123456',
            database='ASTOCK'
        )
        return connection
    except mysql.connector.Error as e:
        print(f"连接MySQL失败: {e}")
        return None

@app.route('/api/zh_stocks', methods=['GET'])
def get_zh_stocks():
    """获取所有可用的股票列表"""
    try:
        connection = create_mysql_connection()
        if not connection:
            return jsonify({'error': '数据库连接失败'}), 500
        
        cursor = connection.cursor()
        cursor.execute("SELECT DISTINCT symbol FROM daily_hfq ORDER BY symbol")
        stocks = [row[0] for row in cursor.fetchall()]
        
        cursor.close()
        connection.close()
        
        return jsonify({'symbols': stocks})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/zh_indexs', methods=['GET'])
def get_zh_indexs():
    """获取所有可用的指数列表"""
    try:
        connection = create_mysql_connection()
        if not connection:
            return jsonify({'error': '数据库连接失败'}), 500
        
        cursor = connection.cursor()
        cursor.execute("SELECT DISTINCT symbol FROM zh_index ORDER BY symbol")
        indexs = [row[0] for row in cursor.fetchall()]
        
        cursor.close()
        connection.close()
        
        return jsonify({'symbols': indexs})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/zh_stocks/bars', methods=['GET'])
def get_zh_stocks_bars():
    """获取K线数据"""
    try:
        symbol = request.args.get('symbol')
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        
        if not symbol or not start_date or not end_date:
            return jsonify({'error': '缺少必要参数'}), 400
        
        # 转换日期格式
        start_dt = datetime.strptime(start_date, '%Y-%m-%d')
        end_dt = datetime.strptime(end_date, '%Y-%m-%d')
        
        connection = create_mysql_connection()
        if not connection:
            return None
        
        cursor = connection.cursor()
        query = """
        SELECT datetime, open_price, high_price, low_price, close_price, volume, turnover
        FROM daily_hfq 
        WHERE symbol = %s AND datetime >= %s AND datetime < %s 
        ORDER BY datetime
        """
        cursor.execute(query, (symbol, start_dt, end_dt))
        results = cursor.fetchall()
        cursor.close()
        connection.close()
        
        # 转换为DataFrame
        df = pd.DataFrame(results, columns=['datetime', 'open_price', 'high_price', 'low_price', 'close_price', 'volume', 'turnover'])
        df.set_index('datetime', inplace=True)
        
        bars_data = []
        for index, row in df.iterrows():
            bars_data.append({
                'time': int(index.timestamp()),
                'open': float(row['open_price']),
                'high': float(row['high_price']),
                'low': float(row['low_price']),
                'close': float(row['close_price']),
                'volume': float(row['volume'])
        })

        return jsonify({'bars': bars_data})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/zh_indexs/bars', methods=['GET'])
def get_zh_indexs_bars():
    """获取K线数据"""
    try:
        symbol = request.args.get('symbol')
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        
        if not symbol or not start_date or not end_date:
            return jsonify({'error': '缺少必要参数'}), 400
        
        # 转换日期格式
        start_dt = datetime.strptime(start_date, '%Y-%m-%d')
        end_dt = datetime.strptime(end_date, '%Y-%m-%d')
        
        connection = create_mysql_connection()
        if not connection:
            return None
        
        cursor = connection.cursor()
        query = """
        SELECT datetime, open_price, high_price, low_price, close_price, volume, turnover
        FROM zh_index 
        WHERE symbol = %s AND datetime >= %s AND datetime < %s 
        ORDER BY datetime
        """
        cursor.execute(query, (symbol, start_dt, end_dt))
        
        
        bars_data = []
        for row in cursor.fetchall():
            bars_data.append({
                'time': int(row[0].timestamp()),
                'open': float(row[1]),
                'high': float(row[2]),
                'low': float(row[3]),
                'close': float(row[4]),
                'volume': float(row[5])
        })

        cursor.close()
        connection.close()        
        return jsonify({'bars': bars_data})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/trades/<project_name>/symbol_list', methods=['GET'])
def get_trades_symbol_list(project_name):
    """获取交易数据"""
    try:
        project = get_project(project_name)
        if not project:
            return jsonify({'error': f'项目 {project_name} 不存在'}), 404
        
        trades_data = data.trade_data_dict.get(project_name, [])
        trades_symbol_list = set()
        for rec in trades_data:
            trades_symbol_list.add(rec['symbol'])

        return jsonify({'trades_symbol_list': list(trades_symbol_list)})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/trades/<project_name>/data', methods=['GET'])
def get_trades_data(project_name):
    """获取交易数据"""
    try:
        symbol = request.args.get('symbol')
        if not symbol:
            return jsonify({'error': '缺少标的代码参数'}), 400
        
        project = get_project(project_name)
        if not project:
            return jsonify({'error': f'项目 {project_name} 不存在'}), 404
                
        # 从全局数据对象获取交易数据
        trade_data = data.trade_data_dict.get(project_name, [])
        
        if not trade_data:
            return jsonify({'trades': []})
        
        symbol_trades_data = [rec for rec in trade_data if rec['symbol'] == symbol]
        result = []
        for rec in symbol_trades_data:
            result.append({
                'time': int(rec['time']),
                'price': float(rec['price']),
                'volume': float(rec['volume']),
                'direction': str(rec['direction']),
                'offset': str(rec['offset'])
            })
        
        return jsonify({'trades': result})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/update_strategy_data', methods=['POST'])
def update_strategy_data():
    """更新策略数据"""
    try:
        request_data = request.get_json()
        project_name = request_data.get('project_name')
        tech_data = request_data.get('tech_data', {})
        trade_data = request_data.get('trade_data', [])
        
        if project_name:
            project = get_project(project_name)
            if not project:
                return jsonify({'error': f'项目 {project_name} 不存在'}), 404
            
            # 更新技术数据
            if tech_data:
                data.tech_data_dict[project_name] = tech_data
            
            # 更新交易数据
            if trade_data:
                trade_df = pd.DataFrame(trade_data)
                if not trade_df.empty:
                    trade_df['datetime'] = pd.to_datetime(trade_df['time'], unit='s')
                    trade_df.set_index('datetime', inplace=True)
                    
            for rec, dt in zip(trade_data, trade_df.index):
                rec['datetime'] = str(dt)
            data.trade_data_dict[project_name] = trade_data
        
        return jsonify({'success': True})
    except Exception as e:
        print(f'update_strategy_data failed: {e}')
        return jsonify({'error': str(e)}), 500

@app.route('/api/zh_stocks/indicators', methods=['GET'])
@app.route('/api/zh_indexs/indicators', methods=['GET'])
def get_target_indicators():
    """获取技术指标数据"""
    try:
        symbol = request.args.get('symbol')
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        indicator = request.args.get('indicator', 'ma5')  # ma5, ma10, ma20, ma60, rsi, macd等
        
        print(f"🔍 技术指标请求: symbol={symbol}, start_date={start_date}, end_date={end_date}, indicator={indicator}")
        
        if not symbol or not start_date or not end_date:
            return jsonify({'error': '缺少必要参数'}), 400
        
        # 转换日期格式
        start_dt = datetime.strptime(start_date, '%Y-%m-%d')
        init_dt = start_dt - timedelta(days=200)
        end_dt = datetime.strptime(end_date, '%Y-%m-%d')
        print(f"📅 日期转换: start_dt={start_dt}, end_dt={end_dt}")
        
        # 获取K线数据
        bars_df = select_target_bars_direct(symbol, init_dt, end_dt)
        
        if bars_df is None or bars_df.empty:
            print(f"❌ 未找到K线数据: symbol={symbol}")
            return jsonify({'error': '未找到数据'}), 404
        
        print(f"✅ 获取到K线数据: {len(bars_df)} 条")
        
        # 转换DataFrame为bars_data格式
        bars_data = []
        for index, row in bars_df.iterrows():
            try:
                bars_data.append({
                    'time': int(index.timestamp()),
                    'open': float(row['open_price']),
                    'high': float(row['high_price']),
                    'low': float(row['low_price']),
                    'close': float(row['close_price']),
                    'volume': int(row['volume'])
                })
            except Exception as e:
                print(f"❌ 转换数据行失败: {e}, row={row}")
                continue
        
        print(f"✅ 转换数据完成: {len(bars_data)} 条")
        
        if len(bars_data) == 0:
            return jsonify({'error': '数据转换失败'}), 500
        
        # 计算所有技术指标
        try:
            all_indicators = calculate_indicators_from_bars(bars_data)
            clean_all_indicators = {}
            end_timestamp = end_dt.timestamp()
            
            for key in all_indicators.keys():
                clean_all_indicators[key] = [daily_value for daily_value in all_indicators[key] if daily_value['time'] < end_timestamp and daily_value['time'] >= start_dt.timestamp()]

            print(f"✅ 计算指标完成: {list(clean_all_indicators.keys())}")
            
            # 打印过滤后的数据统计
            for key, data in clean_all_indicators.items():
                print(f"   {key}: {len(data)} 条数据")
                    
        except Exception as e:
            print(f"❌ 计算指标失败: {e}")
            return jsonify({'error': f'计算指标失败: {str(e)}'}), 500
        
        # 根据请求的指标类型返回数据
        if indicator == 'all_ma':
            ma_results = {
                'ma5': clean_all_indicators['ma5'],
                'ma10': clean_all_indicators['ma10'],
                'ma20': clean_all_indicators['ma20'],
                'ma60': clean_all_indicators['ma60']
            }
            print(f"✅ 返回MA数据: MA={len(ma_results)}")
            return jsonify({'indicator': ma_results})
        elif indicator == 'macd':
            # MACD返回多个系列
            if 'macd' in clean_all_indicators.keys() and 'signal' in clean_all_indicators.keys() and 'histogram' in clean_all_indicators.keys():
                result = {
                    'macd': clean_all_indicators['macd'],
                    'signal': clean_all_indicators['signal'],
                    'histogram': clean_all_indicators['histogram']
                }
                print(f"✅ 返回MACD数据: MACD={len(result['macd'])}, Signal={len(result['signal'])}, Histogram={len(result['histogram'])}")
                return jsonify({'indicator': result})
            else:
                return jsonify({'error': 'MACD数据不可用'}), 500
        elif indicator in clean_all_indicators.keys():
            indicator_data = clean_all_indicators[indicator]
            print(f"✅ 返回指标数据: {indicator}, 数据条数: {len(indicator_data)}")
            return jsonify({'indicator': indicator_data})
        else:
            print(f"❌ 不支持的指标类型: {indicator}")
            return jsonify({'error': f'不支持的指标类型: {indicator}'}), 400
        
    except Exception as e:
        import traceback
        print(f"❌ 技术指标API异常: {e}")
        print(f"详细错误: {traceback.format_exc()}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/health', methods=['GET'])
def health_check():
    """健康检查接口"""
    return jsonify({'status': 'ok', 'message': 'API服务器运行正常'})

@app.route('/api/projects', methods=['GET'])
def get_projects():
    """获取所有注册的项目"""
    try:
        projects = list_projects()
        return jsonify({'projects': projects})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/project/<project_name>', methods=['GET'])
def get_project_summary(project_name):
    """获取指定项目的数据"""
    try:
        project = get_project(project_name)
        if not project:
            return jsonify({'error': f'项目 {project_name} 不存在'}), 404
        
        summary = project.get_summary()
        return jsonify({'project': summary})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/project/<project_name>/data', methods=['GET'])
def get_project_data(project_name):
    """获取指定项目的策略数据"""
    try:
        
        # 返回策略数据
        print(f"data.tech_data_dict[project_name]: {data.tech_data_dict[project_name]}")
        strategy_data = {
            'time': data.tech_data_dict[project_name]['time'],
            'daily_pnl': data.tech_data_dict[project_name]['daily_pnl'],
            'balance': data.tech_data_dict[project_name]['balance'],
            'trades': data.trade_data_dict[project_name],
            'drawdown': data.tech_data_dict[project_name]['drawdown']
        }
        
        return jsonify({'strategy_data': strategy_data})
    except Exception as e:
        print(f"❌ 获取项目数据失败: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/run_project', methods=['POST'])
def run_project():
    """运行指定项目"""
    try:
        data = request.get_json()
        project_name = data.get('project_name')
        start_date = data.get('start_date')
        end_date = data.get('end_date')
        
        print(f"🚀 开始运行项目 {project_name}")
        print(f"📅 时间范围: {start_date} 到 {end_date}")
        
        if not project_name or not start_date or not end_date:
            return jsonify({'error': '缺少必要参数'}), 400
        
        project = get_project(project_name)
        if not project:
            return jsonify({'error': f'项目 {project_name} 不存在'}), 404
        
        print(f"✅ 找到项目: {project_name}")
        
        # 运行项目
        record_df, summary = project.run(start_date, end_date)
        date_list = record_df.index.tolist()
        timestamp_list = [int(time.mktime(date.timetuple())) for date in date_list]
        project.end_balance = summary['end_balance'].item()
        project.max_drawdown = summary['max_drawdown'].item()
        project.max_drawdown_duration = summary['max_drawdown_duration'].item()
        project.total_net_pnl = summary['total_net_pnl'].item()
        project.sharpe_ratio = summary['sharpe_ratio'].item()
        project.time = timestamp_list
        project.daily_pnl = record_df['net_pnl'].tolist()
        project.balance = (record_df['net_pnl'].cumsum() + project.initial_capital).tolist()
        project.drawdown = record_df['drawdown'].tolist()
        project.upload_data()
        
        print(f"🎉 项目 {project_name} 运行完成")
        return jsonify({'success': True, 'message': f'项目 {project_name} 运行完成'})
    except Exception as e:
        print(f"❌ 运行项目失败: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500

@app.route('/api/reload_projects', methods=['POST'])
def reload_projects():
    """重新加载所有项目"""
    try:
        # 清空现有注册表
        PROJECT_REGISTER.clear()
        
        # 重新注册项目
        auto_register_projects()
        
        return jsonify({
            'success': True,
            'message': '项目重新加载成功',
            'projects': list_projects()
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    print("🚀 启动API服务器 (端口8800)...")
    
    auto_register_projects(directory = 'projects')
    
    app.run(debug=True, host='0.0.0.0', port=8800) 